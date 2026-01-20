"""
Overleaf Git utilities for cloning, pulling, and pushing Overleaf projects.
"""

import os
import json
import subprocess
from pathlib import Path
from urllib.parse import quote

_SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_PATH = _SCRIPT_DIR / "memory" / "overleaf_config.json"
OVERLEAF_DIR = _SCRIPT_DIR / "overleaf"


def load_config() -> dict:
    """Load Overleaf configuration from JSON file."""
    if not CONFIG_PATH.exists():
        return {"credentials": {}, "projects": {}}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Save Overleaf configuration to JSON file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_git_url(project_id: str, config: dict) -> str:
    """Build authenticated Git URL for Overleaf project."""
    creds = config.get("credentials", {})
    token = quote(creds.get("password", ""), safe="")
    return f"https://git:{token}@git.overleaf.com/{project_id}"


def add_project(name: str, project_id: str) -> str:
    """Add a new project to the configuration."""
    config = load_config()
    if not config.get("credentials", {}).get("email"):
        return "Error: No credentials configured. Run init_overleaf.py first."

    config.setdefault("projects", {})[name] = {
        "project_id": project_id,
        "local_path": f"overleaf/{name}"
    }
    save_config(config)
    return f"Project '{name}' added with ID {project_id}"


def get_project_path(project_name: str) -> Path:
    """Get the local path for a project."""
    config = load_config()
    project = config.get("projects", {}).get(project_name)
    if not project:
        raise ValueError(f"Project '{project_name}' not found in config")
    return _SCRIPT_DIR / project["local_path"]


def clone_or_pull(project_name: str) -> str:
    """Clone the project if it doesn't exist locally, otherwise pull latest changes."""
    config = load_config()
    project = config.get("projects", {}).get(project_name)
    if not project:
        return f"Error: Project '{project_name}' not found in config"

    project_path = _SCRIPT_DIR / project["local_path"]
    git_url = get_git_url(project["project_id"], config)

    if project_path.exists() and (project_path / ".git").exists():
        # Pull latest changes
        result = subprocess.run(
            ["git", "pull"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return f"Error pulling: {result.stderr}"
        return f"Pulled latest changes for '{project_name}'\n{result.stdout}"
    else:
        # Clone the project
        project_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", git_url, str(project_path)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return f"Error cloning: {result.stderr}"
        return f"Cloned '{project_name}' to {project_path}"


def list_files(project_name: str) -> list[str]:
    """List all files in a project (excluding .git directory)."""
    project_path = get_project_path(project_name)
    if not project_path.exists():
        raise ValueError(f"Project '{project_name}' not cloned. Run pull first.")

    files = []
    for path in project_path.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            files.append(str(path.relative_to(project_path)))
    return sorted(files)


def read_file(project_name: str, file_path: str) -> str:
    """Read a file's content from a project."""
    project_path = get_project_path(project_name)
    full_path = project_path / file_path

    if not full_path.exists():
        raise FileNotFoundError(f"File '{file_path}' not found in project '{project_name}'")

    return full_path.read_text(encoding="utf-8")


def write_file(project_name: str, file_path: str, content: str) -> str:
    """Write content to a file in a project."""
    project_path = get_project_path(project_name)
    full_path = project_path / file_path

    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

    return f"Written {len(content)} characters to {file_path}"


def commit_and_push(project_name: str, message: str) -> str:
    """Stage all changes, commit, and push to Overleaf."""
    project_path = get_project_path(project_name)

    if not project_path.exists():
        return f"Error: Project '{project_name}' not cloned"

    # Stage all changes
    result = subprocess.run(
        ["git", "add", "-A"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return f"Error staging changes: {result.stderr}"

    # Check if there are changes to commit
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    if not status.stdout.strip():
        return "No changes to commit"

    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return f"Error committing: {result.stderr}"

    # Push
    result = subprocess.run(
        ["git", "push"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return f"Error pushing: {result.stderr}"

    return f"Changes pushed to Overleaf: {message}"


def list_projects() -> dict:
    """List all configured projects."""
    config = load_config()
    return config.get("projects", {})

"""
Overleaf MCP Server - Read/write access to Overleaf projects via Git
"""

from fastmcp import FastMCP
import overleaf_utils

mcp = FastMCP("overleaf")


@mcp.tool()
def overleaf_list_projects() -> str:
    """
    List all configured Overleaf projects.

    Returns:
        Formatted list of projects with their IDs and local paths
    """
    try:
        projects = overleaf_utils.list_projects()
        if not projects:
            return "No projects configured. Use overleaf_add_project to add one."

        result = []
        for name, info in projects.items():
            result.append(
                f"Name: {name}\n"
                f"Project ID: {info['project_id']}\n"
                f"Local Path: {info['local_path']}"
            )
        return "\n---\n".join(result)
    except Exception as e:
        return f"Error listing projects: {str(e)}"


@mcp.tool()
def overleaf_add_project(name: str, project_id: str) -> str:
    """
    Add a new Overleaf project to the configuration.

    Args:
        name: A friendly name for the project (e.g., "thesis", "paper")
        project_id: The Overleaf project ID (from the URL: overleaf.com/project/PROJECT_ID)

    Returns:
        Confirmation message
    """
    try:
        return overleaf_utils.add_project(name, project_id)
    except Exception as e:
        return f"Error adding project: {str(e)}"


@mcp.tool()
def overleaf_pull(project: str) -> str:
    """
    Pull latest changes from Overleaf. Clones the project if not already local.

    Args:
        project: The project name (as configured)

    Returns:
        Status message with pull/clone result
    """
    try:
        return overleaf_utils.clone_or_pull(project)
    except Exception as e:
        return f"Error pulling project: {str(e)}"


@mcp.tool()
def overleaf_list_files(project: str) -> str:
    """
    List all files in an Overleaf project.

    Args:
        project: The project name (as configured)

    Returns:
        List of file paths in the project
    """
    try:
        files = overleaf_utils.list_files(project)
        if not files:
            return f"No files found in project '{project}'"
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


@mcp.tool()
def overleaf_read_file(project: str, path: str) -> str:
    """
    Read a file's content from an Overleaf project.

    Args:
        project: The project name (as configured)
        path: Path to the file within the project (e.g., "main.tex")

    Returns:
        The file's content
    """
    try:
        return overleaf_utils.read_file(project, path)
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def overleaf_write_file(project: str, path: str, content: str) -> str:
    """
    Write or update a file in an Overleaf project.

    Args:
        project: The project name (as configured)
        path: Path to the file within the project (e.g., "main.tex")
        content: The content to write to the file

    Returns:
        Confirmation message
    """
    try:
        return overleaf_utils.write_file(project, path, content)
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def overleaf_push(project: str, message: str) -> str:
    """
    Commit and push changes to Overleaf.

    Args:
        project: The project name (as configured)
        message: Commit message describing the changes

    Returns:
        Status message with push result
    """
    try:
        return overleaf_utils.commit_and_push(project, message)
    except Exception as e:
        return f"Error pushing changes: {str(e)}"


if __name__ == "__main__":
    mcp.run()

# Alfred - Personal Assistant for Claude Code

Alfred is an MCP (Model Context Protocol) server that gives Claude Code access to Gmail, Google Calendar, and Overleaf. It's designed to be a personal assistant that can manage emails, schedule events, and edit LaTeX documents directly from the command line.

## Features

- **Gmail**: List, read, star, and send emails
- **Google Calendar**: View and create events
- **Overleaf**: Clone, edit, and push LaTeX projects via Git
- **Memory System**: Persistent notes and context across sessions

## Architecture

Alfred runs as two MCP servers that Claude Code can call:

- `mcp_server.py` - Gmail and Calendar tools
- `overleaf_mcp.py` - Overleaf Git integration

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google OAuth Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Gmail and Calendar APIs
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials as `memory/google_credentials.json`
5. Run the setup script:

```bash
python init_oauth.py
```

### 3. Overleaf Setup (Optional)

1. Get your Git credentials from [Overleaf Settings](https://www.overleaf.com/user/settings) (Git Integration section)
2. Run the setup script:

```bash
python init_overleaf.py
```

### 4. Configure Claude Code

Add the MCP servers to your Claude Code settings (`.mcp.json` or global config):

```json
{
  "mcpServers": {
    "alfred": {
      "command": "fastmcp",
      "args": ["run", "/path/to/alfred/mcp_server.py"]
    },
    "overleaf": {
      "command": "fastmcp",
      "args": ["run", "/path/to/alfred/overleaf_mcp.py"]
    }
  }
}
```

## Available Tools

### Gmail

| Tool | Description |
|------|-------------|
| `gmail_list_emails(query, max_results)` | Search emails with Gmail query syntax |
| `gmail_get_email(email_id)` | Get full email content |
| `gmail_mark_as_read(email_id)` | Mark as read |
| `gmail_star_email(email_id)` | Star for follow-up |
| `gmail_send_email(to, subject, body, cc)` | Send email |

### Calendar

| Tool | Description |
|------|-------------|
| `calendar_get_events(start_date, end_date)` | List events (YYYY-MM-DD format) |
| `calendar_create_event(title, start_time, end_time, description, attendees)` | Create event |

### Overleaf

| Tool | Description |
|------|-------------|
| `overleaf_list_projects()` | List configured projects |
| `overleaf_add_project(name, project_id)` | Add project to config |
| `overleaf_pull(project)` | Clone or pull latest changes |
| `overleaf_list_files(project)` | List project files |
| `overleaf_read_file(project, path)` | Read file content |
| `overleaf_write_file(project, path, content)` | Write/update file |
| `overleaf_push(project, message)` | Commit and push to Overleaf |

## Memory System

Create a `memory/` folder with:

- `about_you.md` - Your identity, preferences, current projects
- `notes.md` - Persistent notes and reminders

Alfred reads these at the start of each session for context. Add instructions in `CLAUDE.md` to tell Claude how to use them.

## Example Usage

Once configured, you can ask Claude Code things like:

- "Check my unread emails"
- "What's on my calendar tomorrow?"
- "Send an email to alice@example.com about the meeting"
- "Pull my thesis project and fix the typo in section 3"

## Cron Automation (Optional)

You can set up automated briefings:

```bash
# Morning briefing at 8am
0 8 * * * cd ~/alfred && claude -p "Good morning! Give me my briefing."

# End of day check at 6pm
0 18 * * * cd ~/alfred && claude -p "Any unread emails I should handle before EOD?"
```

## License

MIT

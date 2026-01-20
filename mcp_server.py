"""
Alfred MCP Server - Gmail and Calendar tools for Claude Code
"""

from fastmcp import FastMCP
from typing import Optional
import google_utils

mcp = FastMCP("alfred")


# ───── Gmail Tools ─────

@mcp.tool()
def gmail_list_emails(query: str = "is:unread", max_results: int = 5) -> str:
    """
    Search and list emails from Gmail.

    Args:
        query: Gmail search query (e.g., "is:unread", "from:someone@email.com", "subject:meeting")
        max_results: Maximum number of emails to return (default: 5)

    Returns:
        Formatted list of emails with id, subject, sender, and snippet
    """
    try:
        emails = google_utils.list_emails(query=query, max_results=max_results)
        if not emails:
            return "No emails found matching the query."

        result = []
        for email in emails:
            result.append(
                f"ID: {email['id']}\n"
                f"From: {email['from']}\n"
                f"Subject: {email['subject']}\n"
                f"Snippet: {email['snippet']}\n"
            )
        return "\n---\n".join(result)
    except Exception as e:
        return f"Error listing emails: {str(e)}"


@mcp.tool()
def gmail_get_email(email_id: str) -> str:
    """
    Get the full content of a specific email by ID.

    Args:
        email_id: The Gmail message ID

    Returns:
        Full email details including body
    """
    try:
        email = google_utils.get_email_by_id(email_id)
        if not email:
            return f"Email with ID {email_id} not found."

        return (
            f"From: {email['from']}\n"
            f"To: {email['to']}\n"
            f"Date: {email['date']}\n"
            f"Subject: {email['subject']}\n\n"
            f"Body:\n{email['body']}"
        )
    except Exception as e:
        return f"Error fetching email: {str(e)}"


@mcp.tool()
def gmail_mark_as_read(email_id: str) -> str:
    """
    Mark an email as read.

    Args:
        email_id: The Gmail message ID

    Returns:
        Confirmation message
    """
    try:
        google_utils.mark_as_read(email_id)
        return f"Email {email_id} marked as read."
    except Exception as e:
        return f"Error marking email as read: {str(e)}"


@mcp.tool()
def gmail_star_email(email_id: str) -> str:
    """
    Star an email for follow-up.

    Args:
        email_id: The Gmail message ID

    Returns:
        Confirmation message
    """
    try:
        google_utils.star_email(email_id)
        return f"Email {email_id} starred."
    except Exception as e:
        return f"Error starring email: {str(e)}"


@mcp.tool()
def gmail_send_email(to: str, subject: str, body: str, cc: Optional[str] = None) -> str:
    """
    Send an email.

    Args:
        to: Recipient email address (or comma-separated addresses)
        subject: Email subject
        body: Email body text
        cc: Optional CC recipients (comma-separated)

    Returns:
        Confirmation message
    """
    try:
        google_utils.send_email(to=to, subject=subject, body_text=body, cc=cc)
        return f"Email sent to {to} with subject: {subject}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


# ───── Calendar Tools ─────

@mcp.tool()
def calendar_get_events(start_date: str, end_date: str) -> str:
    """
    Get calendar events between two dates.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Formatted list of events
    """
    try:
        events = google_utils.get_events_between_dates(start_date, end_date)
        if not events:
            return f"No events found between {start_date} and {end_date}."

        result = []
        for event in events:
            result.append(
                f"Event: {event['summary']}\n"
                f"Start: {event['start']}\n"
                f"End: {event['end']}"
            )
        return "\n---\n".join(result)
    except Exception as e:
        return f"Error fetching events: {str(e)}"


@mcp.tool()
def calendar_create_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    attendees: Optional[str] = None
) -> str:
    """
    Create a calendar event.

    Args:
        title: Event title/summary
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Optional event description
        attendees: Optional comma-separated list of attendee email addresses

    Returns:
        Confirmation message with event link
    """
    try:
        attendees_list = [e.strip() for e in attendees.split(",")] if attendees else None
        result = google_utils.create_event(
            summary=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            attendees_emails=attendees_list
        )
        return result
    except Exception as e:
        return f"Error creating event: {str(e)}"


if __name__ == "__main__":
    mcp.run()

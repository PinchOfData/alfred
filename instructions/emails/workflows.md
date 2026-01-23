# Email & Calendar Instructions

## Gmail Tools

| Tool | Description |
|------|-------------|
| `gmail_list_emails(query, max_results)` | Search emails. Query examples: `is:unread`, `from:someone@email.com`, `subject:meeting` |
| `gmail_get_email(email_id)` | Get full email content by ID |
| `gmail_mark_as_read(email_id)` | Mark email as read |
| `gmail_star_email(email_id)` | Star email for follow-up |
| `gmail_send_email(to, subject, body, cc)` | Send email |

## Calendar Tools

| Tool | Description |
|------|-------------|
| `calendar_get_events(start_date, end_date)` | List events (dates: YYYY-MM-DD) |
| `calendar_create_event(title, start_time, end_time, description, attendees)` | Create event (times: YYYY-MM-DDTHH:MM:SS) |

**Timezone:** All calendar times use Europe/Paris.

## Workflows

### Email Triage

1. List unread emails with `gmail_list_emails("is:unread")`
2. Summarize senders and subjects
3. For important emails, fetch full content with `gmail_get_email`
4. Offer to mark as read or star for follow-up

### Drafting Emails

1. Ask for recipient, subject, and key points if not provided
2. Draft the email and show it for review
3. Only send after explicit confirmation

### Calendar Management

1. When asked about schedule, fetch events for the relevant date range
2. For new events, confirm title, time, and attendees before creating
3. Check for conflicts before scheduling

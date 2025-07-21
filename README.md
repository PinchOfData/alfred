# 🧠 Alfred – Your Personalized AI Assistant

Alfred is an AI assistant designed to help you manage documents, take notes, reply to emails, schedule events, and search the web. It maintains structured memory, supports voice interactions, and responds in a personalized tone that adapts to you over time.

---

## 🚀 Features Overview

### 📄 Document Management
- Upload **PDF** or **TXT** files
- Create and manage plain-text documents
- Summarize and embed content with LLMs for easy retrieval 

### 💬 Conversational Memory
- Natural chat interface with full session history
- Auto-saves key exchanges with `/store` command
- Personalized tone and structured context via `persona.json` and `structured.json`

### 🧠 Note Taking & Cleanup
- Add, list, edit, and delete personal notes
- Auto-save insights detected in conversations
- Clean and de-duplicate notes using LLM reflection

### 🌍 Web & Research Integration
- Google search, Wikipedia, papers, and news summarization
- Visit and summarize any web page

### 📧 Gmail and Google Calendar Integration
- View, flag, draft, and send Gmail messages
- Check out your schedule and create new events
- Built-in editor for composing and reviewing emails/events

### 🔁 Memory & Maintenance
- Easily clear or rebuild memory state
- Tag and retrieve docs/notes on your computer

### 🎙️ Audio I/O Support
- Voice input and text-to-speech responses (optional)

---

## 💻 Command Reference

> Alfred has access to the following commands and will use them if he deems it necessary or you instruct him to do so. You can also use them directly in the chat.

### 🔐 Memory Commands
| Command                     | Action                                          |
|----------------------------|-------------------------------------------------|
| `/store <tag>`             | Save last exchange to memory                    |
| `/lookup <tag> <query>`    | Search memory by tag and query                  |

### 📝 Note Management
| Command                     | Action                                          |
|----------------------------|-------------------------------------------------|
| `/note add <note>`         | Add a new note                                  |
| `/note list`               | List all notes                                  |
| `/note edit <id>`          | Edit a specific note                            |
| `/note del <id>`           | Delete a note                                   |

### 🌐 Web & Research
| Command                     | Action                                          |
|----------------------------|-------------------------------------------------|
| `/search <query>`          | Perform a Google Custom Search                  |
| `/visit <url>`             | Visit and summarize a webpage                   |
| `/wiki <topic>`            | Fetch a Wikipedia summary                       |
| `/papers <query>`          | Get academic paper summaries                    |
| `/news <query>`            | Fetch top news headlines                        |

### 📬 Gmail Commands
| Command                     | Action                                          |
|----------------------------|-------------------------------------------------|
| `/gmail inbox`             | List recent inbox emails                        |
| `/gmail unread`            | Show unread emails                              |
| `/gmail starred`           | Show starred emails                             |
| `/gmail view <msg_id>`     | View full email content                         |
| `/gmail markread <msg_id>` | Mark email as read                              |
| `/gmail star <msg_id>`     | Star an email                                   |
| `/gmail draft`             | Start drafting an email                         |
| `/gmail send`              | Send the current draft                          |

### 📅 Google Calendar Commands

| Command                                                                 | Action                                                                 |
|-------------------------------------------------------------------------|------------------------------------------------------------------------|
| `/calendar events <YYYY-MM-DD> to <YYYY-MM-DD>`                        | List calendar events in a given date range                             |
| `/calendar draft <title> \| <start> \| <end> \| <attendee1,attendee2> \| <description>` | Draft an event (start/end must be in local time format)               |
| `/calendar create`                                                     | Create and send the currently drafted event                            |

> ℹ️ **Time format tip**: Use `YYYY-MM-DDTHH:MM:SS` in **Paris local time** (do not include a `Z` at the end).  
> Example: `2025-07-22T14:00:00` means 2 PM Paris time.

### 📄 Document Commands
| Command                     | Action                                          |
|----------------------------|-------------------------------------------------|
| `/doc new <name>`          | Create a new document                           |
| `/doc write <text>`        | Write or append to document                     |
| `/doc save`                | Save the current document                       |
| `/doc list`                | List all saved documents                        |
| `/doc load <name>`         | Load a document for editing                     |

---

## 📦 Setup Instructions

1. **Clone the project**
   ```bash
   git clone https://github.com/your-username/alfred-assistant.git
   cd alfred-assistant
   ```

2. **Install dependencies**

   ```bash
    pip install -r requirements.txt
    ```

3. **Set environment variables in .env**

   ```bash
    GOOGLE_API_KEY=your_google_api_key
    GOOGLE_CSE_ID=your_custom_search_engine_id
    GROQ_API_KEY=your_groq_api_key
    OPENAI_API_KEY=your_openai_key
    ANTHROPIC_API_KEY=your_anthropic_key
    ```

4. **Run Alfred**
   
   ```bash
    streamlit run app.py
    ```

## 📬 Feedback

This is just me procastinating and trying to figure out how far we can push the current generation of AI models.

Pull requests and suggestions are welcome!

File issues or ideas on GitHub or reach out directly.
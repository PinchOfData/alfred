# 🧠 Alfred – Your Personalized Assistant

Alfred is a memory-augmented AI assistant that helps you summarize documents, query past conversations, take notes, access the web, and more — all while maintaining structured memory and a personalized tone.

---

## 🚀 Features

- 📄 **PDF & TXT Summarization**  
  Upload documents, extract summaries, and search for them at a later point in time.

- 💬 **Conversational Memory**  
  Chat with Alfred — he remembers past messages and stores useful exchanges for a personalized experience.

- 🧠 **Note Management**  
  Add, edit, delete, and clean personal notes with LLM-assisted reflection.

- 🌐 **Web & Research Access**  
  Use commands to access real-time knowledge:
  - `/search <query>` — Google CSE search
  - `/visit <url>` — Visit and summarize any web page
  - `/wiki <topic>` — Get summaries from Wikipedia
  - `/papers <query>` — Academic paper search via Semantic Scholar
  - `/news <topic>` — Top news from Google News RSS

- 🧹 **Memory Tools**  
  Clear session memory or manage long-term ChromaDB memory via `/store`, `/lookup`, and `notes`.

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

## 🛠️ Command Reference

| Command                   | Description                                     |
| ------------------------- | ----------------------------------------------- |
| `/store <tag>`            | Save the last user/assistant exchange to memory |
| `/lookup <tag> <query>`   | Search memory by tag                            |
| `/note add/edit/del/list` | Manage personal notes                           |
| `/search <query>`         | Google search (via Custom Search API)           |
| `/visit <url>`            | Visit and summarize any web page                |
| `/wiki <topic>`           | Fetch Wikipedia summary                         |
| `/papers <topic>`         | Get academic articles via Semantic Scholar      |
| `/news <query>`           | Get top headlines on a topic                    |

## 🧠 Memory and Persistence

- All notes and document memories are stored in memory/ via ChromaDB.

- User memory is structured using persona.json and structured.json.

- Notes can be cleaned using AI to remove duplicates or clarify entries.

## 📬 Feedback

This is just me procastinating and trying to figure out how far we can push the current generation of AI models.

Pull requests and suggestions are welcome!

File issues or ideas on GitHub or reach out directly.
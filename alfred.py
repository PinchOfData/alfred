import streamlit as st
import os
import json
import chromadb
import base64
from chromadb.config import Settings
from utils import (
    load_structured_memory,
    summarize_and_store_pdf,
    load_pdf_by_filename,
    store_text,
    query_memory,
    load_notes,
    add_note,
    edit_note,
    delete_note,
    chat_with_model,
    extract_response_text,
    extract_stream_token,
    detect_tool_use,
    transcribe_audio, 
    synthesize_speech,
    parse_date_range  
)
from web_search import wiki_lookup, search_semantic_scholar
from google_utils import (
    list_emails, 
    send_email, 
    mark_as_read, 
    star_email, 
    get_email_by_id,
    create_event,
    get_events_between_dates
    )

# ───────────── Setup ─────────────

from dotenv import load_dotenv
import os
load_dotenv()
os.environ.get("GROQ_API_KEY")

UPLOAD_DIR = "memory/uploads"
PDF_URL_BASE = "/memory/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Alfred", layout="wide")
MEM_DIR = "memory"
os.makedirs(MEM_DIR, exist_ok=True)

# Load persona and memory
persona = json.load(open(f"{MEM_DIR}/persona.json"))
structured_memory = load_structured_memory(f"{MEM_DIR}/structured.json")

client = chromadb.PersistentClient(
    path=f"{MEM_DIR}/chroma",
    settings=Settings()
)
docs_collection = client.get_or_create_collection(name="documents")
notes_collection = client.get_or_create_collection(name="notes")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "processed_text" not in st.session_state:
    st.session_state.processed_text = ""
if "last_lookup" not in st.session_state:
    st.session_state.last_lookup = {}
if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "pdf_action" not in st.session_state:
    st.session_state.pdf_action = {}
if "draft_doc" not in st.session_state:
    st.session_state.draft_doc = {"filename": None, "content": ""}

# ───────────── Sidebar ─────────────
with st.sidebar:
    st.markdown("## ⚙️ Alfred Settings")

    # LLM selector
    model_choice = st.selectbox(
        "🧠 Choose LLM",
        options=[
            "groq:llama-3.3-70b-versatile",
            "ollama:gemma3",
            "openai:gpt-4o",
            "openai:gpt-4o-mini",
            "openai:o4-mini",
            "openai:o3",
            "anthropic:claude-sonnet-4-0",
            "anthropic:claude-opus-4-0",
            "anthropic:claude-3-5-sonnet-latest"
            "anthropic:claude-3-5-haiku-latest"
        ],
        index=0
    )
    st.session_state.model_choice = model_choice

    # STT model selector
    stt_model = st.selectbox(
        "🎙️ STT (Speech-to-Text) Model",
        options=["groq:whisper-large-v3-turbo", "None"],
        index=0
    )
    st.session_state.stt_model = stt_model

    # TTS model selector
    tts_model = st.selectbox(
        "🔊 TTS (Text-to-Speech) Model",
        options=["None", "groq:playai-tts"],
        index=0
    )
    st.session_state.tts_model = tts_model

    # Memory reset
    if st.button("🧹 Clear Memory"):
        st.session_state.chat_history = []
        st.session_state.processed_text = ""
        st.session_state.latest_draft = ""
        st.session_state.draft_email = None
        st.session_state.draft_doc = {}
        st.session_state.last_lookup = {}
        st.session_state.last_results = []
        st.session_state.pdf_action = {}
        current_key = st.session_state.audio_input_key
        index = int(current_key.split("_")[-1])
        st.session_state.audio_input_key = f"audio_input_{index + 1}"
        st.session_state.audio_already_processed = False        
        st.toast("🧼 All session memory cleared.")

    st.markdown("---")

    st.markdown("## 📄 Upload Document")

    # File uploader
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
    page_numbers = st.text_input("Specify pages (e.g., 1-3,5):", "")

    if uploaded_file and st.button("Summarize and Store"):
        upload_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(upload_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Convert text input to list of pages
        pages = []
        if page_numbers.strip():
            for part in page_numbers.split(","):
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    pages.extend(range(start, end + 1))
                else:
                    pages.append(int(part))

        summary, message = summarize_and_store_pdf(
            uploaded_file,
            docs_collection,
            pages=pages or None,
            model=st.session_state.model_choice
        )
        st.toast(message)
        if summary:
            st.session_state.processed_text = summary
            st.success("Summary added to memory.")

# ───────────── Main Chat Interface ─────────────
st.title("🧠 Alfred")

# ───────────── Chat History ─────────────
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

# ───────────── Chat Interface Input ─────────────

# Text box
text_input = st.chat_input("Ask Alfred or use /command")

# Initialize audio state
if "audio_input_key" not in st.session_state:
    st.session_state.audio_input_key = "audio_input_0"
if "audio_already_processed" not in st.session_state:
    st.session_state.audio_already_processed = False

# Use dynamic key to force audio widget reset when needed
audio_input_key = st.session_state.audio_input_key
audio_bytes = st.audio_input("🎙️ Speak to Alfred", key=audio_input_key)

# Detect new audio and reset flag if needed
if audio_bytes and st.session_state.audio_already_processed:
    st.session_state.audio_already_processed = False

# Prefer transcribed audio (only if new)
user_input = None
if (
    audio_bytes
    and st.session_state.stt_model != "None"
    and not st.session_state.audio_already_processed
):
    with st.spinner("Transcribing audio…"):
        user_input = transcribe_audio(audio_bytes, st.session_state.stt_model)
    st.session_state.audio_already_processed = True
    audio_bytes = None  # prevent local reuse

    # ✅ Bump audio widget key so it resets
    index = int(audio_input_key.split("_")[-1])
    st.session_state.audio_input_key = f"audio_input_{index + 1}"

# Typed input always takes priority
if text_input:
    user_input = text_input
    st.session_state.audio_already_processed = True  # Don't reuse audio after text

def reply_and_save(msg: str):
    with st.chat_message("assistant"):
        st.markdown(msg)
    st.session_state.chat_history.append(("assistant", msg))

if user_input:
    
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # 🧠 Tool detection (before checking for explicit command)
    if not user_input.startswith("/"):
        detected_cmd = detect_tool_use(
            user_input,
            st.session_state.model_choice,
            st.session_state.chat_history  # ✅ pass full chat history
        )
        if detected_cmd:
            user_input = detected_cmd  # Replace with inferred command

    if user_input.startswith("/"):
        # ──────── Commands ────────
        parts = user_input[1:].split(" ", 2)
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if command == "store":
            if args:
                # Combine last user + assistant message, tag it with custom label
                label = args[0]
                chat = st.session_state.chat_history

                # Find last user/assistant exchange
                last_user = next((m[1] for m in reversed(chat) if m[0] == "user"), None)
                last_assistant = next((m[1] for m in reversed(chat) if m[0] == "assistant"), None)

                if last_user and last_assistant:
                    convo = f"User: {last_user}\nAssistant: {last_assistant}"
                    store_text(convo, docs_collection, {"source": "chat", "tag": label})
                    reply_and_save(f"✅ Stored conversation with tag `{label}`.")
                else:
                    reply_and_save("⚠️ No recent conversation to store.")
            else:
                # fallback to storing processed text if no args
                content = st.session_state.processed_text
                if not content.strip():
                    reply_and_save("⚠️ Nothing to store.")
                else:
                    store_text(content, docs_collection, {"source": "user"})
                    reply_and_save("✅ Stored to document collection.")

        elif command == "rebuild":
            import glob
            from utils import summarize_and_store_pdf, load_pdf_by_filename, embed_full_text, save_notes
            from datetime import datetime

            # Step 1: Clear ChromaDB collections
            for coll in [docs_collection, notes_collection]:
                all_ids = coll.get().get("ids", [])
                if all_ids:
                    coll.delete(ids=all_ids)

            reply_and_save("🧹 Cleared existing ChromaDB collections.")

            # Step 2: Rebuild docs_collection from PDFs
            pdf_dir = "memory/uploads"
            pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
            for pdf_path in pdf_files:
                try:
                    with open(pdf_path, "rb") as f:
                        from io import BytesIO
                        fake_upload = BytesIO(f.read())
                        fake_upload.name = os.path.basename(pdf_path)

                        summary, msg = summarize_and_store_pdf(
                            fake_upload,
                            docs_collection,
                            model=st.session_state.model_choice,
                            pages=[1]  # default to first page
                        )
                        st.toast(f"✅ Indexed PDF: {fake_upload.name}")
                except Exception as e:
                    st.warning(f"❌ Failed to index {pdf_path}: {e}")

            # Step 3: Rebuild docs_collection from text files
            doc_dir = "memory/docs"
            all_files = glob.glob(os.path.join(doc_dir, "*.*"))
            for txt_path in all_files:
                try:
                    with open(txt_path, "r") as f:
                        content = f.read()
                    filename = os.path.basename(txt_path)
                    store_text(content, docs_collection, {
                        "tag": "doc",
                        "filename": filename
                    })
                    st.toast(f"✅ Indexed text doc: {filename}")
                except Exception as e:
                    st.warning(f"❌ Failed to index {txt_path}: {e}")

            # Step 4: Rebuild notes_collection from notes.json
            notes_path = os.path.join("memory", "notes.json")
            if os.path.exists(notes_path):
                try:
                    with open(notes_path, "r") as f:
                        notes_data = json.load(f)

                    for note in notes_data:
                        add_note(note["content"], notes_collection)

                    st.toast(f"✅ Restored {len(notes_data)} notes.")
                except Exception as e:
                    st.warning(f"⚠️ Could not load notes: {e}")

            reply_and_save("🔁 Rebuild complete. ChromaDB is now reindexed.")

        elif command == "calendar":
            sub = args[0] if args else ""

            if sub == "events":
                if len(args) >= 3 and args[1].lower() == "events":
                    date_range = " ".join(args[2:]).strip()
                else:
                    date_range = " ".join(args[1:]).strip()

                try:
                    start_date, end_date = parse_date_range(date_range)
                    events = get_events_between_dates(start_date, end_date)

                    if not events:
                        reply_and_save(f"📭 No events found between {start_date} and {end_date}.")
                    else:
                        lines = [f"**{e['summary']}**\n🕐 {e['start']} — {e['end']}" for e in events]
                        reply_and_save("📅 **Events Found:**\n\n" + "\n\n".join(lines))

                except Exception as e:
                    reply_and_save(f"❌ Could not parse date range or list events: {e}")

            elif sub == "draft":

                full_raw = user_input.split(" ", 2)[-1] if len(user_input.split(" ", 2)) == 3 else ""
                parts  = [p.strip() for p in full_raw.split("|")]

                if len(parts ) < 4:
                    reply_and_save("⚠️ Usage: `/calendar draft <title> | <start> | <end> | <attendee1,attendee2> | <description>`")
                else:
                    try:
                        event = {
                            "summary": parts[0],
                            "start": parts[1],
                            "end": parts[2],
                            "attendees": [a.strip() for a in parts[3].split(",") if a.strip()],
                            "description": parts[4] if len(parts) > 4 else ""
                        }
                        st.session_state.draft_event = event
                        reply_and_save(f"""📝 **Event Drafted**

                        **Title**: {event['summary']}  
                        **Start**: {event['start']}  
                        **End**: {event['end']}  
                        **Attendees**: {", ".join(event['attendees']) or "(None)"}  
                        **Description**: {event['description'] or "(None)"}

                        Use `/calendar create` to confirm.
                        """)
                    except Exception as e:
                        reply_and_save(f"❌ Error drafting event: {e}")

            elif sub == "create":
                event = st.session_state.get("draft_event")
                if not event:
                    reply_and_save("⚠️ No event draft found. Use `/calendar draft` first.")
                else:
                    try:
                        result = create_event(
                            summary=event["summary"],
                            start_time=event["start"],
                            end_time=event["end"],
                            description=event["description"],
                            attendees_emails=event["attendees"]
                        )
                        st.session_state.draft_event = None
                        reply_and_save(result)
                    except Exception as e:
                        reply_and_save(f"❌ Failed to create event: {e}")

        elif command == "lookup":
            if len(args) < 2:
                reply_and_save("⚠️ Usage: `/lookup <tag> <your query>` (e.g., `/lookup pdf how does it work`)")
            else:
                tag = args[0]
                query = args[1]

                # Query ChromaDB
                results = query_memory(query, docs_collection, top_k=5)
                tagged_results = [r for r in results if r[1].get("tag") == tag]

                if not tagged_results:
                    reply_and_save(f"🤷 No results found for tag `{tag}`.")
                else:
                    st.session_state.last_lookup = {"tag": tag, "query": query}
                    st.session_state.last_results = tagged_results
                    reply_and_save(f"🔎 Found {len(tagged_results)} result(s) for `{tag}`.")

        elif command == "news":
            query = args[0] if args else "top news today"

            from web_search import get_news_articles
            articles = get_news_articles(query)

            content = "\n\n".join([f"{i+1}. {a['title']}\n{a['summary']}" for i, a in enumerate(articles)])
            prompt = f"""
            You are a helpful assistant. The user asked for a news update on: {query}.

            Summarize the following headlines in a few bullet points.

            News content:
            {content}
            """

            response = chat_with_model(
                st.session_state.model_choice,
                messages=[{"role": "system", "content": prompt}],
                stream=False
            )

            provider = st.session_state.model_choice.split(":")[0]
            summary = extract_response_text(response, provider)

            # Build article list with links
            article_links = "\n\n".join([
                f"[{i+1}. {a['title']}]({a['link']})"
                for i, a in enumerate(articles)
            ])

            reply_and_save("🗞️ **News Digest — {}**".format(query.title()))
            reply_and_save("### Summary:\n" + summary)
            reply_and_save("### Top Articles:\n" + article_links)

        elif command == "search":
            from web_search import google_search
            query = " ".join(args)
            if not query:
                reply_and_save("⚠️ Usage: `/search <your query>`")
            else:
                try:
                    results = google_search(query)
                except Exception as e:
                    reply_and_save(f"❌ Error fetching search: {e}")
                    results = []

                if not results:
                    reply_and_save("🤷 No results found.")
                else:
                    formatted = "\n\n".join([
                        f"**{r['title']}**\n{r['summary']}\n[🔗 Read More]({r['link']})\nTo summarize: `/visit {r['link']}`"
                        for r in results
                    ])
                    reply_and_save(f"🔍 Google Search Results for: `{query}`\n\n{formatted}")

        elif command == "visit":
            from web_search import fetch_and_clean_url
            url = args[0] if args else ""
            if not url.startswith("http"):
                reply_and_save("⚠️ Usage: `/visit <valid url>`")
            else:
                page_text = fetch_and_clean_url(url)
                if not page_text or page_text.startswith("⚠️"):
                    reply_and_save(page_text or "❌ Failed to fetch page.")
                else:
                    # Optional: truncate if very long
                    max_chars = 80000
                    trimmed_page = page_text[:max_chars]

                    # Store in context (used in full prompt)
                    st.session_state.processed_text = trimmed_page

                    reply_and_save(f"🧠 Loaded webpage content from [{url}]({url}) into Alfred’s context memory.")

        elif command == "wiki":
            from web_search import wiki_lookup
            query = " ".join(args)
            if not query:
                reply_and_save("⚠️ Usage: `/wiki <topic>`")
            else:
                result = wiki_lookup(query)
                if "error" in result:
                    reply_and_save(result["error"])
                else:
                    reply_and_save(f"📚 **{result['title']}**\n\n{result['summary']}\n\n[🔗 Wikipedia]({result['url']})")

        elif command == "papers":
            from web_search import search_semantic_scholar
            query = " ".join(args)
            if not query:
                reply_and_save("⚠️ Usage: `/papers <topic>`")
            else:
                papers = search_semantic_scholar(query)
                if isinstance(papers, dict) and "error" in papers:
                    reply_and_save(papers["error"])
                elif not papers:
                    reply_and_save("❌ No academic papers found.")
                else:
                    formatted = "\n\n".join([
                        f"**{p['title']}** ({p['year']}) — {p['authors']}\n"
                        f"📄 {p['abstract']}\n"
                        f"[🔗 Link]({p['url']}) — 🧠 {p['citations']} citations"
                        for p in papers
                    ])
                    reply_and_save(f"📚 Top Papers for: `{query}`\n\n{formatted}")

        elif command == "doc":
            sub = args[0] if args else ""
            
            if sub == "new" and len(args) >= 2:
                st.session_state.draft_doc = {"filename": args[1], "content": ""}
                reply_and_save(f"📝 New document started: `{args[1]}`")

            elif sub == "write":
                text = args[1] if len(args) >= 2 else ""
                if not text:
                    reply_and_save("⚠️ Provide text to write.")
                else:
                    st.session_state.draft_doc["content"] = text.strip()
                    reply_and_save("✅ Text added to document.")

            elif sub == "save":
                filename = st.session_state.draft_doc["filename"]
                content = st.session_state.draft_doc["content"]

                if filename and content:
                    save_path = os.path.join("memory", "docs", filename)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, "w") as f:
                        f.write(content)

                    # Store summary or embedding in Chroma
                    store_text(content, docs_collection, metadata={
                        "tag": "doc",
                        "filename": filename
                    })

                    reply_and_save(f"✅ Document `{filename}` saved.")
                else:
                    reply_and_save("⚠️ No document to save.")

            elif sub == "list":
                doc_dir = os.path.join("memory", "docs")
                if os.path.exists(doc_dir):
                    docs = [f for f in os.listdir(doc_dir) if os.path.isfile(os.path.join(doc_dir, f))]
                    reply_and_save("📁 Saved Documents:\n" + "\n".join(f"- {d}" for d in docs))
                else:
                    reply_and_save("📂 No saved documents found.")

            elif sub == "load" and len(args) >= 2:
                fname = args[1]
                doc_path = os.path.join("memory", "docs", fname)
                if os.path.exists(doc_path):
                    with open(doc_path, "r") as f:
                        content = f.read()
                    st.session_state.draft_doc = {"filename": fname, "content": content}
                    reply_and_save(f"📂 Loaded `{fname}` into memory.")
                else:
                    reply_and_save(f"❌ File `{fname}` not found.")

            else:
                reply_and_save("⚠️ Usage: `/doc new|write|save|list|load`")

        elif command == "gmail":
            sub = args[0] if args else ""
            
            if sub == "inbox":
                parts = command.split()
                sub = parts[1] if len(parts) > 1 else "inbox"
                count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 5

                emails = list_emails("in:inbox", max_results=count)
                reply = "\n\n".join([f"⭐ *{e['subject']}*\nFrom: {e['from']}\n{e['snippet']}\nID: `{e['id']}`" for e in emails])
                reply_and_save(reply or "📭 No inbox emails.")
            
            elif sub == "unread":
                parts = command.split()
                sub = parts[1] if len(parts) > 1 else "inbox"
                count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 5

                emails = list_emails("is:unread", max_results=count)
                reply = "\n\n".join([f"📧 *{e['subject']}*\nFrom: {e['from']}\n{e['snippet']}\nID: `{e['id']}`" for e in emails])
                reply_and_save(reply or "📭 No unread emails.")

            elif sub == "starred":
                parts = command.split()
                sub = parts[1] if len(parts) > 1 else "inbox"
                count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 5

                emails = list_emails("is:starred", max_results=count)
                reply = "\n\n".join([f"⭐ *{e['subject']}*\nFrom: {e['from']}\n{e['snippet']}\nID: `{e['id']}`" for e in emails])
                reply_and_save(reply or "✨ No starred emails.")

            elif sub == "view":
                email_id = args[1] if len(args) > 1 else None

                if email_id:
                    email = get_email_by_id(email_id)
                    if email:
                        reply = (
                            f"📧 **{email['subject']}**\n"
                            f"**From:** {email['from']}\n"
                            f"**To:** {email.get('to', 'N/A')}\n"
                            f"**Date:** {email.get('date', 'N/A')}\n\n"
                            f"---\n\n"
                            f"{email['body']}\n\n"
                            f"---\n\n"
                            f"🆔 `{email['id']}`"
                        )
                    else:
                        reply = f"❌ Email with ID `{email_id}` not found."
                else:
                    reply = "⚠️ Please provide a valid email ID to view."

                reply_and_save(reply)

            elif sub == "markread":
                if len(args) < 2:
                    reply_and_save("⚠️ Usage: `/gmail markread <msg_id>`")
                else:
                    mark_as_read(args[1])
                    reply_and_save("✅ Email marked as read.")

            elif sub == "star":
                if len(args) < 2:
                    reply_and_save("⚠️ Usage: `/gmail star <msg_id>`")
                else:
                    star_email(args[1])
                    reply_and_save("⭐ Email starred.")

            elif sub == "draft":
                full_input = " ".join(args[1:])
                parts = [p.strip() for p in full_input.split("|")]

                to = None
                cc = None
                subject = None
                body_parts = []

                try:
                    for part in parts:
                        label, sep, value = part.partition(":")
                        key = label.strip().lower()
                        value = value.strip()

                        if sep != ":" or not value:
                            if not to:
                                to = part.strip()
                            else:
                                body_parts.append(part.strip())
                        elif key == "to":
                            to = value
                        elif key == "cc":
                            cc = [email.strip() for email in value.split(",") if email.strip()]
                        elif key == "subject":
                            subject = value
                        else:
                            body_parts.append(part.strip())

                    if not to or not subject or not body_parts:
                        reply_and_save("⚠️ Usage: `/gmail draft <to> | cc:<cc1,cc2> | subject:<subject> | <body>` (CC optional)")
                    else:
                        st.session_state.draft_email = {
                            "to": to,
                            "cc": cc,
                            "subject": subject.strip(),
                            "body": "\n".join(body_parts).strip()
                        }

                        reply_and_save(f"""📄 **Draft Created**

            **To**: {to}  
            **CC**: {', '.join(cc) if cc else '(None)'}  
            **Subject**: {subject.strip()}  
            **Body**:  
            {st.session_state.draft_email['body']}

            Use `/gmail send` to send it when ready.
            """)
                except Exception as e:
                    reply_and_save(f"❌ Error creating draft: {e}")

            elif sub == "editdraft":
                if "draft_email" not in st.session_state or not st.session_state.draft_email:
                    reply_and_save("⚠️ No draft available to edit.")
                else:
                    full_input = " ".join(args[1:])
                    parts = [p.strip() for p in full_input.split("|")]

                    updated_fields = {}
                    body_parts = []

                    try:
                        for part in parts:
                            label, sep, value = part.partition(":")
                            key = label.strip().lower()
                            value = value.strip()

                            if sep != ":" or not value:
                                # If there's no colon or it's malformed, treat as body text
                                body_parts.append(part.strip())
                            elif key == "to":
                                updated_fields["to"] = value
                            elif key == "cc":
                                updated_fields["cc"] = [email.strip() for email in value.split(",") if email.strip()]
                            elif key == "subject":
                                updated_fields["subject"] = value
                            else:
                                # Treat unrecognized labels as body content fallback
                                body_parts.append(part.strip())

                        if body_parts:
                            updated_fields["body"] = "\n".join(body_parts).strip()

                        for key, val in updated_fields.items():
                            st.session_state.draft_email[key] = val

                        reply_and_save("✅ Draft updated with fields: " + ", ".join(updated_fields.keys()))
                    except Exception as e:
                        reply_and_save(f"❌ Error editing draft: {e}")

            elif sub == "send":
                draft = st.session_state.get("draft_email")
                if draft:
                    try:
                        send_email(
                            to=draft["to"],
                            subject=draft["subject"],
                            body_text=draft["body"],
                            cc=draft.get("cc")
                        )
                        reply_and_save(f"📤 Sent email to `{draft['to']}`.")
                        st.session_state.draft_email = None
                    except Exception as e:
                        reply_and_save(f"❌ Failed to send email: {e}")
                else:
                    reply_and_save("⚠️ No draft found. Use `/gmail draft <to> | <subject> | <body>` first.")

            else:
                reply_and_save("⚠️ Usage: `/gmail inbox|unread|starred|send|markread|star`")

        elif command == "note":
            if not args:
                reply_and_save("Usage: `/note add|edit|del|list`")
            else:
                subcommand = args[0]
                if subcommand == "add":
                    text = args[1] if len(args) > 1 else ""
                    if not text:
                        reply_and_save("⚠️ Provide note text.")
                    else:
                        add_note(text, notes_collection)
                        reply_and_save("📝 Note added.")
                elif subcommand == "edit":
                    if len(args) < 3:
                        reply_and_save("Usage: `/note edit 0 new text`")
                    else:
                        idx = int(args[1])
                        new_text = args[2]
                        if edit_note(idx, new_text, notes_collection):
                            reply_and_save("✏️ Note edited.")
                        else:
                            reply_and_save("❌ Invalid index.")
                elif subcommand == "del":
                    idx = int(args[1]) if len(args) > 1 else -1
                    if delete_note(idx):
                        reply_and_save("🗑️ Note deleted.")
                    else:
                        reply_and_save("❌ Invalid index.")
                elif subcommand == "list":
                    notes = load_notes()
                    if notes:
                        reply_and_save("\n".join(f"**{i}** — {n['content']}" for i, n in enumerate(notes)))
                    else:
                        reply_and_save("_No notes saved yet._")
                elif subcommand == "clean":
                    notes = load_notes()
                    if not notes:
                        reply_and_save("_No notes to clean._")
                    else:
                        summaries = "\n".join(f"- {n['content']}" for n in notes)
                        cleanup_prompt = f"""
                        You are a thoughtful assistant tasked with cleaning up notes.

                        Here are the notes:
                        {summaries}

                        Identify:
                        1. Redundant or overlapping notes
                        2. Notes that can be combined or clarified
                        3. Notes that seem unclear or unnecessary

                        Return an updated Python list of cleaned notes. If any notes are to be removed, explain why briefly at the end.

                        Only return the new list.
                        """

                        response = chat_with_model(
                            st.session_state.model_choice,
                            messages=[{"role": "system", "content": cleanup_prompt}],
                            stream=False
                        )

                        provider = st.session_state.model_choice.split(":")[0]
                        cleaned_notes_text = extract_response_text(response, provider)

                        # Show cleaned version before saving
                        reply_and_save(f"🧹 Cleaned Notes:\n{cleaned_notes_text}")

                        # Extract only the notes (lines starting with "- ")
                        import ast

                        # Try to extract the list safely
                        try:
                            list_start = cleaned_notes_text.find("[")
                            list_end = cleaned_notes_text.find("]", list_start) + 1
                            list_str = cleaned_notes_text[list_start:list_end]
                            cleaned_notes = ast.literal_eval(list_str)
                            assert isinstance(cleaned_notes, list)
                        except Exception as e:
                            cleaned_notes = []
                            st.warning(f"⚠️ Could not parse cleaned notes list: {e}")

                    if cleaned_notes:
                        # Clear current ChromaDB notes collection
                        all_notes = notes_collection.get()
                        all_ids = all_notes.get("ids", [])

                        if all_ids:
                            notes_collection.delete(ids=all_ids)

                        # Save new notes (with explicit IDs)
                        for note in cleaned_notes:
                            add_note(note, notes_collection)

                        # Optional: sync cleaned notes to JSON file
                        from utils import save_notes
                        from datetime import datetime
                        save_notes([
                            {"timestamp": datetime.now().isoformat(), "content": n} for n in cleaned_notes
                        ])

                        st.toast("✅ Notes cleaned and re-saved.")
                    else:
                        reply_and_save("⚠️ No cleaned notes were extracted to save.")

                else:
                    reply_and_save("Unknown note command.")

        else:
            reply_and_save("❌ Unknown command.")

    else:
        # ──────── Full Prompt Construction ────────
        draft_doc = st.session_state.get("draft_doc", {})
        draft_text = draft_doc.get("content", "").strip()
        draft_filename = draft_doc.get("filename", "Untitled Draft")

        processed_text = st.session_state.get("processed_text", "").strip()
        notes_text = "\n".join(f"- {note}" for note in query_memory(user_input, notes_collection, top_k=5)) or "None"
        memory_prompt = "\n".join(f"{k}: {v}" for k, v in structured_memory.items())

        # Build email section
        email = st.session_state.get("draft_email")
        email_text = ""
        if email:
            email_text = f"""To: {email.get("to", "N/A")}
        CC: {", ".join(email.get("cc", [])) if email.get("cc") else "None"}
        Subject: {email.get("subject", "N/A")}

        {email.get("body", "").strip()}"""

        # Build structured prompt
        sections = [
            f"You are {persona['name']}, a {persona['role']}.",
            f"Tone: {persona['tone']}",
            f"Style: {persona['style']}",
            "",
            "### 🧠 User Details",
            memory_prompt,
            "",
            "### 📓 Notes",
            notes_text
        ]

        if processed_text:
            sections.extend([
                "",
                "### 📄 Uploaded Document",
                processed_text
            ])

        if draft_text:
            sections.extend([
                "",
                f"### ✍️ Draft Document: {draft_filename}",
                draft_text
            ])

        if email_text.strip():
            sections.extend([
                "",
                "### 📧 Draft Email",
                email_text
            ])

        full_prompt = "\n".join(sections)

        # Show prompt in expandable block
        with st.expander("🔍 Full Prompt", expanded=False):
            st.code(full_prompt.strip(), language="markdown")

        # Stream response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            answer = ""
            chat_messages = [{"role": "system", "content": full_prompt}]
            for role, msg in st.session_state.chat_history:
                if role in {"user", "assistant"}:
                    chat_messages.append({"role": role, "content": msg})
            chat_messages.append({"role": "user", "content": user_input})

            stream = chat_with_model(
                st.session_state.model_choice,
                messages=chat_messages,
                stream=True,
            )

            provider = st.session_state.model_choice.split(":")[0]
            for chunk in stream:
                token = extract_stream_token(chunk, provider)
                answer += token
                placeholder.markdown(answer + "▌")

            placeholder.markdown(answer)       
        st.session_state.chat_history.append(("assistant", answer))

        if st.session_state.tts_model != "None":
            audio_data = synthesize_speech(answer, st.session_state.tts_model)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")

        # After assistant response (answer is complete)
        top_notes = query_memory("User:{}\n Assistant:{}".format(user_input, answer), notes_collection, top_k=3)

        existing_notes = "\n".join(f"- {n}" for n in top_notes) or "None"

        note_check_prompt_intro = """
        You are a helpful assistant aiming to personalize the user experience by saving useful insights for future reference.

        Instructions:
        - Focus on **user experience** and **information about the user's life**, not technical details.
        - Return a standalone note or "NO_NOTE" — nothing else.
        """

        note_check_prompt_user_input = f"""
        Here are saved notes:
        {existing_notes}

        Interaction:
        User: {user_input}
        Assistant: {answer}
        """

        note_response = chat_with_model(
            st.session_state.model_choice,
            messages=[
                {"role": "system", "content": note_check_prompt_intro},
                {"role": "user", "content": note_check_prompt_user_input}
            ],
            stream=False
        )

        provider = st.session_state.model_choice.split(":")[0]
        note_text = extract_response_text(note_response, provider)

        if note_text != "NO_NOTE":
            add_note(note_text, notes_collection)
            st.toast("📝 Alfred saved a note automatically.")

# ───────────── Document Editor ─────────────
if st.session_state.get("draft_doc", {}).get("filename"):
    st.subheader("📄 Document Editor")

    st.text_input(
        "✏️ Filename",
        value=st.session_state.draft_doc["filename"],
        key="doc_edit_filename",
        disabled=True
    )

    st.session_state.draft_doc["content"] = st.text_area(
        "📝 Content",
        value=st.session_state.draft_doc["content"],
        height=300,
        key="doc_edit_content"
    )

    st.markdown("💾 Use `/doc save` to store your changes.")

# ───────────── Draft Event Editor ─────────────
if st.session_state.get("draft_event"):
    ev = st.session_state.draft_event
    st.subheader("📅 Review & Edit Draft Event")

    st.session_state.draft_event["summary"] = st.text_input("📝 Title", value=ev["summary"])
    st.session_state.draft_event["start"] = st.text_input("🕐 Start Time", value=ev["start"])
    st.session_state.draft_event["end"] = st.text_input("🕒 End Time", value=ev["end"])
    st.session_state.draft_event["attendees"] = st.text_input("👥 Attendees (comma-separated)", value=", ".join(ev["attendees"])).split(",")
    st.session_state.draft_event["description"] = st.text_area("🗒️ Description", value=ev["description"], height=100)

    st.markdown("📤 Use `/calendar create` to confirm and send the invite.")

# ───────────── Draft Email Editor ─────────────
if st.session_state.get("draft_email"):
    draft = st.session_state.draft_email
    st.subheader("📧 Review & Edit Draft Email")

    st.markdown(f"**To:** `{draft.get('to')}`")

    st.session_state.draft_email["to"] = st.text_input(
        "📬 To", value=draft.get("to", ""), key="edit_to"
    )

    st.session_state.draft_email["cc"] = st.text_input(
        "📋 CC (comma-separated)", value=", ".join(draft.get("cc", [])), key="edit_cc"
    ).split(",") if st.session_state.draft_email["cc"] else []

    st.session_state.draft_email["subject"] = st.text_input(
        "✏️ Subject", value=draft.get("subject", ""), key="edit_subject"
    )
    st.session_state.draft_email["body"] = st.text_area(
        "📝 Body", value=draft.get("body", ""), height=200, key="edit_body"
    )

    st.markdown("➡️ When you're ready, type `/gmail send` to send the email.")

# ───────────── Display Lookup Results in Tabs ─────────────
if user_input and not user_input.startswith("/lookup "):
    st.session_state.last_lookup = {}
    st.session_state.last_results = []

if st.session_state.last_results:
    st.subheader(f"🔎 Lookup Results for `{st.session_state.last_lookup.get('tag')}`")

    tabs = st.tabs([
        f"{meta.get('filename') or meta.get('tag') or f'Result {i+1}'}"
        for i, (_, meta) in enumerate(st.session_state.last_results)
    ])

    for i, tab in enumerate(tabs):
        summary, meta = st.session_state.last_results[i]
        with tab:
            st.markdown(summary)

            is_pdf = "filename" in meta and meta["filename"].lower().endswith(".pdf")

            # Load into context for all results
            if st.button("📥 Load into context", key=f"load_{i}"):
                st.session_state.processed_text = summary[:80000]
                st.toast("✅ Loaded result into memory.")

            # Preview only for PDFs
            if is_pdf:
                if st.button("👁️ Preview", key=f"preview_{i}"):
                    st.session_state.pdf_action = {"type": "preview", "file": meta["filename"]}

# ───────────── Handle PDF Action (Load / Preview) ─────────────
action = st.session_state.pdf_action
if action:
    fname = action.get("file")
    if action["type"] == "load":
        text = load_pdf_by_filename(fname)
        if text:
            trimmed_text = text[:80000]

            st.session_state.processed_text = trimmed_text
            st.toast(f"✅ Loaded the first 80,000 characters from `{fname}`.")
        else:
            st.warning("⚠️ Could not load text from PDF.")
    elif action["type"] == "preview":
        file_path = os.path.join(UPLOAD_DIR, fname)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                pdf_url = f"data:application/pdf;base64,{b64}"
                js = f"<script>window.open('{pdf_url}', '_blank')</script>"
                st.components.v1.html(js, height=0)
        else:
            st.warning("⚠️ File not found for preview.")

    st.session_state.pdf_action = {}  # Clear action after handling
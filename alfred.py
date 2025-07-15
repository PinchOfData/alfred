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
    synthesize_speech
)

# ───────────── Setup ─────────────

from dotenv import load_dotenv
import os
load_dotenv()
os.environ.get("GROQ_API_KEY")

STATIC_UPLOAD_DIR = "static/uploads"
PDF_URL_BASE = "/static/uploads"
os.makedirs(STATIC_UPLOAD_DIR, exist_ok=True)

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
            "anthropic:claude-3-sonnet-20240229"
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
        upload_path = os.path.join(STATIC_UPLOAD_DIR, uploaded_file.name)
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
if audio_bytes and st.session_state.stt_model != "None" and not st.session_state.audio_already_processed:
    with st.spinner("Transcribing audio…"):
        user_input = transcribe_audio(audio_bytes, st.session_state.stt_model)
    st.session_state.audio_already_processed = True

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
        detected_cmd = detect_tool_use(user_input, st.session_state.model_choice)
        if detected_cmd:
            st.session_state.chat_history.append(("assistant", f"_Detected tool request → `{detected_cmd}`_"))
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
                    max_chars = 10000
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
        memory_prompt = "\n".join(f"{k}: {v}" for k, v in structured_memory.items())
        top_notes = query_memory(user_input, notes_collection, top_k=5)
        notes_text = "\n".join(f"- {note}" for note in top_notes) or "None"
        pdf_text = st.session_state.processed_text.strip()

        full_prompt = f"""
        You are {persona['name']}, a {persona['role']}.

        Your tone is: {persona['tone']}
        Your communication style: {persona['style']}

        User details:
        {memory_prompt}

        Notes:
        {notes_text}

        Recent Document Content:
        {pdf_text or 'No document provided.'}

        Now answer this in your own voice: {user_input}
        """


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
        - Focus on **user experience**, not technical details.
        - Return a standalone note or "NO_NOTE" — nothing else.
        """

        note_check_prompt_user_input = f"""
        Here are saved notes:
        {existing_notes}

        Interaction:
        User: {user_input}
        Assistant: {answer}
        """

#        with st.expander("🧾 Note Reflection Prompt", expanded=False):
#            st.code(note_check_prompt.strip(), language="markdown")

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
            st.markdown(summary[:400] + "...")

            if "filename" in meta:
                if st.button("📥 Load into context", key=f"load_{i}"):
                    st.session_state.pdf_action = {"type": "load", "file": meta["filename"]}
                if st.button("👁️ Preview", key=f"preview_{i}"):
                    st.session_state.pdf_action = {"type": "preview", "file": meta["filename"]}
            else:
                if st.button("📥 Load into context", key=f"textload_{i}"):
                    st.session_state.processed_text = summary[:10000]
                    st.toast("✅ Loaded result into memory.")
                with st.expander("👁️ View Full Text"):
                    st.markdown(summary)

# ───────────── Handle PDF Action (Load / Preview) ─────────────
action = st.session_state.pdf_action
if action:
    fname = action.get("file")
    if action["type"] == "load":
        text = load_pdf_by_filename(fname)
        if text:
            trimmed_text = text[:10000]

            st.session_state.processed_text = trimmed_text
            st.toast(f"✅ Loaded the first 10,000 characters from `{fname}`.")
        else:
            st.warning("⚠️ Could not load text from PDF.")
    elif action["type"] == "preview":
        file_path = os.path.join(STATIC_UPLOAD_DIR, fname)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                pdf_url = f"data:application/pdf;base64,{b64}"
                js = f"<script>window.open('{pdf_url}', '_blank')</script>"
                st.components.v1.html(js, height=0)
        else:
            st.warning("⚠️ File not found for preview.")

    st.session_state.pdf_action = {}  # Clear action after handling
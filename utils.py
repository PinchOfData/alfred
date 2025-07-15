import os, json, uuid, fitz          # PyMuPDF
from datetime import datetime
from sentence_transformers import SentenceTransformer
from ollama import chat as ollama_chat
from PIL import Image
import io
import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


# ───────────────── Embeddings ──────────────────
model = SentenceTransformer("all-MiniLM-L6-v2")   # fast & light

def embed_chunks(text: str, chunk_size: int = 512):
    """Return [[chunk, embedding], …]"""
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    embeddings = model.encode(chunks)
    return list(zip(chunks, embeddings))

def embed_full_text(text: str):
    return model.encode([text])[0]

# ───────────────── PDF / TXT helpers ───────────
def extract_text(uploaded_file, pages: list[int] | None = None) -> str:
    """Read PDF or TXT, optionally only the pages given (1-based)."""
    if uploaded_file.name.endswith(".pdf"):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        if pages:
            pages = [p - 1 for p in pages]               # fitz is 0-based
            text = "\n".join(doc[p].get_text() for p in pages if p < len(doc))
        else:
            text = "\n".join(page.get_text() for page in doc)
    elif uploaded_file.name.endswith(".txt"):
        text = uploaded_file.read().decode()
    else:
        text = ""
    return text

def store_text(text: str, collection, metadata: dict | None = None):
    """Store one text object (no chunking) in Chroma."""
    record = dict(
        documents=[text],
        embeddings=[embed_full_text(text)],
        ids=[str(uuid.uuid4())],
    )
    if metadata:                       # ← only send if non-empty
        record["metadatas"] = [metadata]

    collection.add(**record)

def summarize_and_store_pdf(uploaded_file, collection, model="gemma3:latest", pages=None):
    """Extracts text (optionally from selected pages), summarizes it, stores summary in Chroma."""
    filename = uploaded_file.name

    # Extract only the specified pages
    full_text = extract_text(uploaded_file, pages=pages)

    if not full_text.strip():
        return None, "❌ No text could be extracted."

    # Summarize the document
    prompt = f"Summarize this document clearly and concisely for retrieval:\n\n{full_text}"
    summary = ask_model(prompt, model_name=model)

    if not summary.strip():
        return None, "❌ Summarization failed."

    # Store summary in ChromaDB
    store_text(summary, collection, metadata={
        "tag": "pdf",
        "filename": filename
    })

    return summary, f"✅ Summary stored for: `{filename}`"

def render_pdf_preview(filename: str, max_pages: int = 3):
    """Render up to `max_pages` of a saved PDF and show them as images in Streamlit."""
    path = os.path.join("memory", "uploads", filename)

    if not os.path.exists(path):
        st.warning("⚠️ File not found.")
        return

    doc = fitz.open(path)
    total_pages = len(doc)

    for page_num in range(min(total_pages, max_pages)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # higher res
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        st.image(img, caption=f"{filename} — Page {page_num + 1}")

def load_pdf_by_filename(filename: str) -> str | None:
    """Load a previously uploaded PDF by filename and extract its text."""
    path = os.path.join("static", "uploads", filename)

    if not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        return extract_text(f)

# ───────────────── Memory search ───────────────
def load_structured_memory(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r") as f:
        return json.load(f)

def query_memory(query: str, collection, top_k: int = 3) -> list[tuple[str, dict]]:
    e = embed_full_text(query)
    res = collection.query(query_embeddings=[e], n_results=top_k)
    
    documents = res["documents"][0] if res["documents"] else []
    metadatas = res["metadatas"][0] if res.get("metadatas") else [{}] * len(documents)

    return list(zip(documents, metadatas))

# ───────────────── Notes ───────────────────────
NOTES_FILE = "memory/notes.json"

def load_notes() -> list[dict]:
    try:
        with open(NOTES_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_notes(notes: list[dict]):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)


def add_note(text: str, notes_collection=None):
    note_id = str(uuid.uuid4())  # generate a stable unique ID

    # Save locally
    notes = load_notes()
    notes.append({
        "timestamp": datetime.now().isoformat(),
        "content": text.strip(),
        "id": note_id  # optional: store ID locally too
    })
    save_notes(notes)

    # Save to ChromaDB with explicit ID
    if notes_collection:
        notes_collection.add(
            documents=[text.strip()],
            metadatas=[{"kind": "note"}],
            ids=[note_id]
        )

def edit_note(idx: int, new_text: str, notes_collection=None):
    notes = load_notes()
    if 0 <= idx < len(notes):
        notes[idx]["content"] = new_text.strip()
        save_notes(notes)
        if notes_collection:
            # naïve: just add new embedding; cleaning old one is left to future GC
            store_text(new_text, notes_collection)
        return True
    return False

def delete_note(idx: int):
    notes = load_notes()
    if 0 <= idx < len(notes):
        notes.pop(idx)
        save_notes(notes)
        return True
    return False

# ───────────────── LLMs ─────────────

def chat_with_model(model_name: str, messages: list, stream: bool = False):
    """
    Dispatch chat messages to a selected provider.

    Supported providers:
    - ollama:<model>
    - groq:<model>
    - openai:<model>
    - anthropic:<model>

    Returns:
        Response object or streaming generator.
    """
    import os
    provider, model = model_name.split(":", 1)

    if provider == "ollama":
        import ollama
        if stream:
            return ollama.chat(model=model, messages=messages, stream=True)
        else:
            return ollama.chat(model=model, messages=messages, stream=False)

    elif provider == "groq":
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        return client.chat.completions.create(model=model, messages=messages, stream=stream)

    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return client.chat.completions.create(model=model, messages=messages, stream=stream)

    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Extract system message if present
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_content = "\n".join([
            m["content"] if m["role"] == "user" else f"Assistant: {m['content']}"
            for m in messages if m["role"] in {"user", "assistant"}
        ])
        message_block = [{"role": "user", "content": user_content}]

        if stream:
            def stream_generator():
                with client.messages.stream(
                    model=model,
                    system=system_msg,
                    messages=message_block,
                    max_tokens=1024,
                ) as stream_resp:
                    for chunk in stream_resp.text_stream:
                        yield {"message": {"content": chunk}}
            return stream_generator()
        else:
            response = client.messages.create(
                model=model,
                system=system_msg,
                messages=message_block,
                max_tokens=1024,
            )
            return {"message": {"content": response.content[0].text}}

    else:
        raise ValueError(f"Unsupported provider: '{provider}'")

def ask_model(prompt: str, model_name="ollama:gemma3:latest"):
    messages = [{"role": "user", "content": prompt}]
    resp = chat_with_model(model_name, messages, stream=False)
    if model_name.startswith("ollama:"):
        return resp["message"]["content"].strip()
    else:
        return resp.choices[0].message.content.strip()

def extract_response_text(response, provider: str) -> str:
    """
    Extracts the main assistant message from a model response.

    Args:
        response: The model's response object.
        provider: One of 'openai', 'groq', 'ollama', 'anthropic'.

    Returns:
        A clean text string.
    """
    if provider in ("openai", "groq"):
        return response.choices[0].message.content.strip()

    elif provider == "ollama":
        return response["message"]["content"].strip()

    elif provider == "anthropic":
        return response["message"]["content"].strip()

    else:
        raise ValueError(f"Unknown provider: {provider}")
    
def extract_stream_token(chunk, provider: str) -> str:
    """
    Extracts a token from a streamed chunk depending on provider.

    Returns an empty string if nothing is found.
    """
    if provider in {"ollama", "anthropic"}:
        return chunk.get("message", {}).get("content", "") or ""
    elif provider in {"openai", "groq"}:
        if hasattr(chunk.choices[0], "delta"):
            return getattr(chunk.choices[0].delta, "content", "") or ""
    return ""

# ───────────────── Tool detection ──────────────

def detect_tool_use(user_input: str, model_name: str) -> str | None:
    """
    Use LLM to detect if the user's input is a tool invocation.
    If so, return the corresponding command string (e.g., "/wiki Einstein").
    Otherwise, return None.
    """
    import json

    tools = {
        "/lookup <tag> <query>": "Search internal memory (NB: tags are lowercase and optional)",
        "/wiki <topic>": "Summarize a Wikipedia article",
        "/papers <topic>": "Search academic literature",
        "/news <topic?>": "Summarize current news (NB: topic is optional)",
        "/search <query>": "Perform a web search",
        "/visit <url>": "Navigate to a webpage URL"
    }

    tool_list = "\n".join([f"- `{cmd}` — {desc}" for cmd, desc in tools.items()])

    prompt = f"""
    You have access to many tools:
    {tool_list}

    Your job:
    1. Determine if the user intends to **invoke a tool**.
    2. If yes, respond with a well-formed command.
    3. If the user is just chatting (not asking Alfred to take action), respond only with:
    NO_COMMAND

    Examples:
    - "Tell me who Karl Popper was" → `/wiki Karl Popper`
    - "Look up papers about diffusion models" → `/papers diffusion models`
    - "Summarize this URL: https://foo.com" → `/visit https://foo.com`
    - "What are my upcoming tasks?" → NO_COMMAND

    The user said:
    \"\"\"{user_input}\"\"\"    

    Now respond:
    """

    response = chat_with_model(
        model_name,
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )

    if model_name.startswith(("ollama:", "anthropic:")):
        result = response["message"]["content"].strip()
    else:
        result = response.choices[0].message.content.strip()

    return None if result.upper() == "NO_COMMAND" else result

# ───────────────── Audio Transcription ──────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def transcribe_audio(audio_bytes: bytes, model_name: str) -> str:
    """
    Transcribes audio using OpenAI or GroqCloud Whisper models.

    Args:
        audio_bytes: Raw audio file bytes (WAV format).
        model_name: A string like "openai:whisper-1" or "groq:whisper-large-v3-turbo".

    Returns:
        Transcribed text.
    """
    import io
    from openai import OpenAI
    import os

    provider, model = model_name.split(":", 1)

    if provider not in {"openai", "groq"}:
        raise ValueError(f"STT only supported via OpenAI or GroqCloud, not: {provider}")

    api_key = os.getenv("OPENAI_API_KEY") if provider == "openai" else os.getenv("GROQ_API_KEY")
    base_url = "https://api.openai.com/v1" if provider == "openai" else "https://api.groq.com/openai/v1"

    if not api_key:
        raise ValueError(f"{provider.upper()}_API_KEY is missing.")

    client = OpenAI(api_key=api_key, base_url=base_url)
    audio_file = ("audio.wav", audio_bytes, "audio/wav")

    response = client.audio.transcriptions.create(
        model=model,
        file=audio_file
    )
    return response.text.strip()

def synthesize_speech(text: str, tts_model: str = "groq:playai-tts", voice: str = "Atlas-PlayAI") -> bytes:
    """
    Converts text to speech using PlayAI via GroqCloud.

    Args:
        text: Input text to synthesize.
        tts_model: Model name (must start with 'groq:' currently).
        voice: Voice name for synthesis.

    Returns:
        Audio content as bytes.
    """
    from openai import OpenAI
    import os

    provider, model = tts_model.split(":", 1)

    if provider != "groq":
        raise ValueError("TTS currently only supported via GroqCloud PlayAI.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing.")

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text
    )
    return response.content
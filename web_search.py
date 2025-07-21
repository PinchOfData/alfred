import requests
from bs4 import BeautifulSoup
import wikipedia
import os

# ─────────────────────────────────────
# /news (Google News RSS)
# ─────────────────────────────────────
def get_news_articles(query="top news today"):
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, features="xml")
    items = soup.findAll("item")

    results = []
    for item in items[:5]:
        results.append({
            "title": item.title.text,
            "link": item.link.text,
            "summary": item.description.text
        })
    return results

# ─────────────────────────────────────
# /search (Google CSE)
# ─────────────────────────────────────
def google_search(query, num_results=5):
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        raise ValueError("GOOGLE_API_KEY or GOOGLE_CSE_ID not set in environment.")

    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": num_results,
    }

    response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    if response.status_code != 200:
        raise RuntimeError(f"Google Search API Error: {response.text}")

    results = response.json().get("items", [])
    return [
        {
            "title": r["title"],
            "link": r["link"],
            "summary": r.get("snippet", "")
        }
        for r in results
    ]

# ─────────────────────────────────────
# /visit (Fetch + Clean Page Text)
# ─────────────────────────────────────
from playwright.sync_api import sync_playwright

def fetch_and_clean_url(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            page.wait_for_load_state("networkidle")  # ensure page is fully loaded

            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = " ".join(chunk.strip() for chunk in soup.stripped_strings)
        return text[:15000]

    except Exception as e:
        return f"⚠️ Failed to fetch JS-rendered page: {e}"


# ─────────────────────────────────────
# /wiki (Wikipedia Summary)
# ─────────────────────────────────────
import wikipedia

# Ensure default language
wikipedia.set_lang("en")

def wiki_lookup(query, sentences=5):
    try:
        # First, try to get a page object directly
        page = wikipedia.page(query, auto_suggest=True, redirect=True)
        summary = wikipedia.summary(page.title, sentences=sentences, auto_suggest=False, redirect=True)
        return {
            "title": page.title,
            "summary": summary,
            "url": page.url
        }
    except wikipedia.exceptions.DisambiguationError as e:
        return {
            "error": f"🔍 That search is ambiguous. Try one of: {', '.join(e.options[:5])}..."
        }
    except wikipedia.exceptions.PageError:
        return {
            "error": f"❌ No exact Wikipedia page found for: '{query}'"
        }
    except Exception as e:
        return {
            "error": f"⚠️ Unexpected error: {e}"
        }

# ─────────────────────────────────────
# /papers (Semantic Scholar)
# ─────────────────────────────────────
def search_semantic_scholar(query, limit=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,abstract,url,citationCount"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        papers = response.json().get("data", [])
    except Exception as e:
        return {"error": f"⚠️ Failed to fetch papers: {e}"}

    results = []
    for p in papers:
        results.append({
            "title": p.get("title", "Unknown Title"),
            "authors": ", ".join(a.get("name", "") for a in p.get("authors", [])),
            "year": p.get("year", "n.d."),
            "abstract": p.get("abstract", "No abstract available."),
            "url": p.get("url", ""),
            "citations": p.get("citationCount", 0)
        })

    return results

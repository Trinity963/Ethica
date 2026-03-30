# ============================================================
# Ethica v0.1 — web_search.py
# WebSearch Module — sovereign search via DuckDuckGo
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

from pathlib import Path
import sys

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR.parent.parent))

# ── Tool: web_search ──────────────────────────────────────────
def web_search(input_str):
    """Search DuckDuckGo — returns top 5 results."""
    query = input_str.strip()
    if not query:
        return "WebSearch — no query provided."
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(
                    f"📄 {r['title']}\n"
                    f"   {r['href']}\n"
                    f"   {r['body'][:200]}...\n"
                )
        if not results:
            return f"WebSearch — no results for: {query}"
        header = f"WebSearch — {query}\n{'─'*40}\n"
        return header + "\n".join(results)
    except Exception as e:
        return f"WebSearch — error: {e}"

# ── Tool: web_news ───────────────────────────────────────────
def web_news(input_str):
    """Search DuckDuckGo News — returns top 5 news articles."""
    query = input_str.strip()
    if not query:
        return "WebSearch News — no query provided."
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=5):
                date = r.get('date', '')[:10]
                results.append(
                    f"📰 {r['title']} [{date}]\n"
                    f"   {r['url']}\n"
                    f"   {r['body'][:200]}...\n"
                )
        if not results:
            return f"WebSearch News — no results for: {query}"
        header = f"WebSearch News — {query}\n{'─'*40}\n"
        return header + "\n".join(results)
    except Exception as e:
        return f"WebSearch News — error: {e}"

# ── Tool: web_fetch ───────────────────────────────────────────
def web_fetch(input_str):
    """Fetch and extract readable text from a URL."""
    url = input_str.strip()
    if not url:
        return "WebFetch — no URL provided."
    try:
        import urllib.request
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self._skip = False
            def handle_starttag(self, tag, attrs):
                if tag in ('script', 'style', 'nav', 'footer'):
                    self._skip = True
            def handle_endtag(self, tag):
                if tag in ('script', 'style', 'nav', 'footer'):
                    self._skip = False
            def handle_data(self, data):
                if not self._skip and data.strip():
                    self.text.append(data.strip())

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        parser = TextExtractor()
        parser.feed(html)
        text = ' '.join(parser.text)
        # Truncate to 2000 chars
        if len(text) > 2000:
            text = text[:2000] + "\n... [truncated]"
        return f"WebFetch — {url}\n{'─'*40}\n{text}"
    except Exception as e:
        return f"WebFetch — error: {e}"

# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "web_search": web_search,
    "web_fetch":  web_fetch,
    "web_news":   web_news,
}
def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[WebSearch] Unknown tool: {tool_name}"

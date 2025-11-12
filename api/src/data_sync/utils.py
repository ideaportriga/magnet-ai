import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md


def clean_text(text: str) -> str:
    # Remove invalid or garbage characters
    text = text.replace("\u0e00", " ")
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]", " ", text)
    text = re.sub(r"[\uf020-\uf074\ufffe]", " ", text)
    # Remove unnecessary punctuation
    text = re.sub(r"['\"’“”:()\[\]{}]", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove leading and trailing whitespace
    return text.strip()


def parse_page(page_content: str, base_url: str):
    soup = BeautifulSoup(page_content, "html.parser")

    for anchor in soup.find_all("a", href=True):
        if isinstance(anchor, Tag):
            href = anchor.get("href")
            if isinstance(href, str) and href.startswith("/"):
                absolute_url = urljoin(base_url, href)
                anchor["href"] = absolute_url

    # replace the Unicode character \u200b (a zero-width space) with an empty string
    clean_html = str(soup).replace("\u200b", "")

    # Convert HTML to Markdown preserving structure (headings, lists, links, etc.)
    page_text = md(clean_html, heading_style="ATX", bullets="-")

    return page_text

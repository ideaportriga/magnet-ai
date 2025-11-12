import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from html2text import HTML2Text


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
    # page_text = soup.get_text().replace("\u200b", "")
    clean_html = str(soup).replace("\u200b", "")

    # convert to markdown
    h = HTML2Text()
    h.body_width = 0
    page_text = h.handle(clean_html)

    return page_text

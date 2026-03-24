import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from kreuzberg import ExtractionConfig, extract_bytes


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


async def parse_page(page_content: str, base_url: str):
    soup = BeautifulSoup(page_content, "html.parser")

    for anchor in soup.find_all("a", href=True):
        if isinstance(anchor, Tag):
            href = anchor.get("href")
            if isinstance(href, str) and href.startswith("/"):
                absolute_url = urljoin(base_url, href)
                anchor["href"] = absolute_url

    clean_html = str(soup).replace("\u200b", "")

    config = ExtractionConfig(output_format="markdown")
    result = await extract_bytes(clean_html.encode("utf-8"), "text/html", config=config)
    return result.content

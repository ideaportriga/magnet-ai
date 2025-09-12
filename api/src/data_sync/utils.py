import re


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

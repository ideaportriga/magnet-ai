import logging
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from data_sources.data_source import DataSource

logger = logging.getLogger(__name__)


class DocumentationPage:
    """Represents a single documentation page"""

    def __init__(self, url: str, title: str, content: str, language: str, section: str):
        self.url = url
        self.title = title
        self.content = content
        self.language = language
        self.section = section

    def __repr__(self):
        return f"DocumentationPage(url={self.url}, title={self.title}, lang={self.language})"


class VitePressDataSource(DataSource[DocumentationPage]):
    """Data source for VitePress documentation sites.

    This data source crawls documentation pages from a VitePress site,
    following links within specified sections and languages.
    """

    def __init__(
        self,
        base_url: str,
        languages: List[str] = None,
        sections: List[str] = None,
        section_start_urls: Dict[str, str] = None,
        max_depth: int = 5,
    ) -> None:
        """Initialize VitePress data source.

        Args:
            base_url: Base URL of the VitePress site (e.g., http://localhost:5173)
            languages: List of language codes to crawl (e.g., ['en', 'ru'])
            sections: List of sections to crawl (e.g., ['quickstarts', 'admin'])
            section_start_urls: Dict mapping section names to specific start URLs
            max_depth: Maximum crawl depth to prevent infinite loops
        """
        self._base_url = base_url.rstrip("/")
        self._languages = languages or ["en"]
        self._sections = sections or ["quickstarts", "admin"]
        self._section_start_urls = section_start_urls or {}
        self._max_depth = max_depth
        self._visited_urls: Set[str] = set()
        self._pages: List[DocumentationPage] = []
        self._base_path = urlparse(self._base_url).path

    @property
    def name(self) -> str:
        return "VitePress Documentation"

    @property
    def source_description(self) -> str:
        """Provides a description of the data source."""
        return (
            f"VitePress Documentation Source crawling {len(self._languages)} languages "
            f"and {len(self._sections)} sections from {self._base_url}"
        )

    async def get_data(self) -> List[DocumentationPage]:
        """Crawl the VitePress documentation and return all pages.

        Returns:
            List of DocumentationPage objects
        """
        logger.info(f"Starting documentation crawl from {self._base_url}")

        # Build starting URLs for each language
        # We'll start from the language root and then filter by sections
        start_urls = []
        for lang in self._languages:
            # Pattern: /docs/{lang}/
            lang_url = f"{self._base_url}/docs/{lang}/"
            start_urls.append((lang_url, lang))

        # Crawl from each starting URL
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            for url, lang in start_urls:
                logger.info(f"Crawling language: {lang}")
                # Crawl all sections for this language
                for section in self._sections:
                    await self._crawl_section(client, url, lang, section, depth=0)

        logger.info(f"Crawl complete. Found {len(self._pages)} documentation pages.")
        return self._pages

    async def _crawl_section(
        self,
        client: httpx.AsyncClient,
        lang_url: str,
        language: str,
        section: str,
        depth: int,
    ) -> None:
        """Crawl a specific section by first finding links in the language root page.

        Args:
            client: HTTP client for making requests
            lang_url: Language root URL (e.g., /docs/en/)
            language: Language code
            section: Section name to filter
            depth: Current crawl depth
        """
        logger.info(f"Crawling section '{section}' for language '{language}'")

        # First, fetch the language root page to find section links
        try:
            logger.debug(f"Fetching language root: {lang_url}")
            response = await client.get(lang_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find all links that belong to this section
            section_links = self._find_section_links(soup, lang_url, language, section)

            logger.info(
                f"Found {len(section_links)} starting links for section '{section}'"
            )

            # If no links found, try configured start URL or common entry points
            if not section_links:
                # Check if user provided a specific start URL for this section
                if section in self._section_start_urls:
                    start_url = self._section_start_urls[section]
                    logger.info(
                        f"Using configured start URL for section '{section}': {start_url}"
                    )
                    section_links = [start_url]
                else:
                    logger.warning(
                        f"No links found for section '{section}' on root page. Trying common entry points..."
                    )
                    section_links = await self._try_common_entry_points(
                        client, language, section
                    )

            # Crawl each link in the section
            for link in section_links:
                await self._crawl_recursive(client, link, language, section, depth)

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {lang_url}: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"Request error fetching {lang_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {lang_url}: {e}")

    async def _crawl_recursive(
        self,
        client: httpx.AsyncClient,
        url: str,
        language: str,
        section: str,
        depth: int,
    ) -> None:
        """Recursively crawl documentation pages.

        Args:
            client: HTTP client for making requests
            url: URL to crawl
            language: Language code for this page
            section: Section name for this page
            depth: Current crawl depth
        """
        # Check depth limit
        if depth > self._max_depth:
            logger.debug(f"Max depth reached for {url}")
            return

        # Check if already visited
        if url in self._visited_urls:
            return

        # Mark as visited
        self._visited_urls.add(url)

        try:
            logger.debug(f"Fetching: {url}")
            response = await client.get(url)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract page title
            title = self._extract_title(soup)

            # Extract main content
            content = self._extract_content(soup)

            if content:
                # Create page object
                page = DocumentationPage(
                    url=url,
                    title=title,
                    content=content,
                    language=language,
                    section=section,
                )
                self._pages.append(page)
                logger.info(f"Added page: {title} ({url})")

            # Find and follow links within the same section
            links = self._extract_links(soup, url, language, section)
            for link in links:
                await self._crawl_recursive(client, link, language, section, depth + 1)

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"Request error fetching {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error crawling {url}: {e}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Page title
        """
        # Try to find h1 first
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        # Fall back to title tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        return "Untitled"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from VitePress page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted text content
        """
        # VitePress typically uses a main content area with class .content or .vp-doc
        content_area = (
            soup.find("div", class_="vp-doc")
            or soup.find("main")
            or soup.find("article")
        )

        if not content_area:
            # Fall back to body if specific content area not found
            content_area = soup.find("body")

        if not content_area:
            return ""

        # Remove script and style elements
        for element in content_area(["script", "style", "nav", "footer"]):
            element.decompose()

        # Get text content
        text = content_area.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    def _find_section_links(
        self, soup: BeautifulSoup, lang_url: str, language: str, section: str
    ) -> List[str]:
        """Find all links that belong to a specific section from the language root page.

        Args:
            soup: BeautifulSoup object of the language root page
            lang_url: Language root URL
            language: Language code
            section: Section name to filter

        Returns:
            List of absolute URLs in this section
        """
        links = set()

        # Pattern: {base_path}/docs/{language}/{section}/...
        section_pattern = f"{self._base_path}/docs/{language}/{section}/"

        # Find all links
        all_links = soup.find_all("a", href=True)
        logger.debug(f"Found {len(all_links)} total links on {lang_url}")

        for a_tag in all_links:
            href = a_tag["href"]
            logger.debug(f"Processing link: {href}")

            # Convert to absolute URL
            absolute_url = urljoin(lang_url, href)

            # Parse URL
            parsed = urlparse(absolute_url)

            # Remove fragment and query
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            # Check if link belongs to this section
            if parsed.path.startswith(section_pattern):
                logger.debug(f"Found section link: {clean_url}")
                # Ensure it's an HTML page
                if clean_url.endswith((".html", "/")):
                    links.add(clean_url)
            else:
                logger.debug(
                    f"Link does not match section pattern {section_pattern}: {parsed.path}"
                )

        logger.info(f"Found {len(links)} links matching section '{section}'")
        return list(links)

    async def _try_common_entry_points(
        self, client: httpx.AsyncClient, language: str, section: str
    ) -> List[str]:
        """Try common entry point URLs for a section when no links are found.

        Args:
            client: HTTP client for making requests
            language: Language code
            section: Section name

        Returns:
            List of valid entry point URLs
        """
        # Common patterns for section entry points
        patterns = [
            f"{self._base_url}/docs/{language}/{section}/",
            f"{self._base_url}/docs/{language}/{section}/index.html",
            f"{self._base_url}/docs/{language}/{section}/overview.html",
            f"{self._base_url}/docs/{language}/{section}/introduction.html",
            f"{self._base_url}/docs/{language}/{section}/getting-started.html",
        ]

        valid_urls = []

        for url in patterns:
            try:
                logger.debug(f"Trying entry point: {url}")
                response = await client.head(url, timeout=5.0)
                if response.status_code == 200:
                    logger.info(f"Found valid entry point: {url}")
                    valid_urls.append(url)
                    break  # Use the first valid entry point
            except Exception as e:
                logger.debug(f"Entry point not available: {url} - {e}")
                continue

        if valid_urls:
            logger.info(f"Using entry point(s): {valid_urls}")
        else:
            logger.warning(f"No valid entry points found for section '{section}'")

        return valid_urls

    def _extract_links(
        self, soup: BeautifulSoup, current_url: str, language: str, section: str
    ) -> List[str]:
        """Extract relevant documentation links from the page.

        Args:
            soup: BeautifulSoup object
            current_url: Current page URL
            language: Current language
            section: Current section

        Returns:
            List of absolute URLs to follow
        """
        links = []

        # Find all links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]

            # Convert to absolute URL
            absolute_url = urljoin(current_url, href)

            # Parse URL
            parsed = urlparse(absolute_url)

            # Remove fragment and query
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            # Only follow links within the same section and language
            # Pattern: {base_path}/docs/{language}/{section}/...
            expected_prefix = f"{self._base_path}/docs/{language}/{section}/"

            if (
                parsed.path.startswith(expected_prefix)
                and clean_url not in self._visited_urls
            ):
                # Ensure it's an HTML page (ends with .html or is a directory)
                if clean_url.endswith((".html", "/")):
                    links.append(clean_url)

        return links

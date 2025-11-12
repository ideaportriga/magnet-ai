import datetime
from typing import Any

import httpx

from data_sources.data_source import DataSource


class HubspotDataSource(DataSource[dict]):
    def __init__(
        self, chunk_size: int = 2000, page_limit: int = 10, api_token: str | None = None
    ) -> None:
        """Initializes the HubspotDataSource with the provided chunk size and page limit.

        Args:
            chunk_size (int, optional): Maximum number of records to process at a time. Defaults to 2000.
            page_limit (int, optional): Number of records to fetch per API request. Defaults to 100.
            api_token (str, optional): HubSpot API token. If not provided, falls back to environment variable.

        """
        self.max_chunk_size = chunk_size
        self.page_limit = page_limit

        # Use provided token or fall back to environment
        if api_token:
            self.token = api_token
        else:
            from core.config._utils import get_env

            self.token = get_env("KNOWLEDGE_SOURCE_HUBSPOT", "")()

        self.base_url = "https://api.hubapi.com"

    @property
    def name(self) -> str:
        return "Hubspot"

    async def _get_list_of_knowledge_articles(
        self,
        offset: int = 0,
        type=["KNOWLEDGE_ARTICLE", "BLOG_POST", "LANDING_PAGE"],
    ) -> dict[str, Any]:
        """Fetches a list of knowledge articles from HubSpot with pagination support.

        Args:
            offset (int, optional): The starting point for fetching records. Defaults to 0.

        Returns:
            Dict[str, Any]: JSON response containing the list of knowledge articles.

        """
        url = f"{self.base_url}/cms/v3/site-search/search"

        params = {
            "q": "o OR a",  # workaround - how to retrieve all records. (hubspot doesn't have documentation for query param and this param is mandatory)
            "limit": self.page_limit,  # Adjust as needed or use self.page_limit
            "offset": offset,
            "type": type,
        }
        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        return data

    async def _fetch_additional_content(
        self,
        record_id: str,
        record_type: str,
    ) -> dict[str, Any]:
        """Fetches additional content for a specific record.

        Args:
            record_id (str): Unique identifier of the record.
            record_type (str): Type of the record.

        Returns:
            Dict[str, Any]: JSON response containing additional content or an empty dict in case of an error.

        """
        api_url = f"{self.base_url}/cms/v3/site-search/indexed-data/{record_id}?type={record_type}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError:
            # Optional: Implement logging here
            # print(f"Error fetching content for ID {record_id}: {e}")
            return {}

    def _extract_content(self, content_json: dict[str, Any]) -> str:
        """Extracts and combines content from the 'html_other_nested.en' field.

        Args:
            content_json (Dict[str, Any]): JSON response containing the content.

        Returns:
            str: Combined content or an empty string if not available.

        """
        fields = content_json.get("fields", {})
        html_other_nested = fields.get("html_other_nested.en", {})
        values = html_other_nested.get("values", [])
        if isinstance(values, list):
            return "\n".join(values)
        return ""

    def _extract_published_date(self, content_json: dict[str, Any]) -> str:
        """Extracts the publishedDate value from the record and converts it to ISO format.

        Args:
            content_json (Dict[str, Any]): JSON response containing the content.

        Returns:
            str: Published date in ISO 8601 format or an empty string if not available.

        """
        fields = content_json.get("fields", {})
        published_date = fields.get("publishedDate", {})
        timestamp_ms = published_date.get("value", 0)
        if timestamp_ms == 0:
            return ""
        try:
            # Convert milliseconds to seconds for datetime
            dt = datetime.datetime.utcfromtimestamp(timestamp_ms / 1000)
            return dt.isoformat() + "Z"  # Append 'Z' to indicate UTC
        except (ValueError, OSError, OverflowError):
            return ""

    async def get_data(self) -> list[dict[str, Any]]:
        """Retrieves and returns a list of records with additional 'content' and 'publishedDate' fields.

        Returns:
            List[Dict[str, Any]]: List of enriched records.

        """
        enriched_records = []

        offset = 0
        total = None  # Will be set after the first request

        while True:
            initial_data = await self._get_list_of_knowledge_articles(offset=offset)
            if total is None:
                total = initial_data.get("total", 0)

            records = initial_data.get("results", [])

            if not records:
                break  # No more records to process

            for record in records:
                record_id = str(record.get("id", ""))
                record_type = record.get("type", "")

                if not record_id or not record_type:
                    continue  # Skip if essential fields are missing

                # Fetch additional content
                content_json = await self._fetch_additional_content(
                    record_id, record_type
                )
                content = self._extract_content(content_json)
                published_date = self._extract_published_date(content_json)

                # Add 'content' and 'publishedDate' to the record
                record["content"] = content
                record["publishedDate"] = published_date

                enriched_records.append(record)

            # Update offset for the next page
            offset += self.page_limit

            # Break the loop if we've fetched all records
            if offset >= total:
                offset = 0
                break

        return enriched_records

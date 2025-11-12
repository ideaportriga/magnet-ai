from logging import getLogger

import httpx

from data_sources.data_source import DataSource
from data_sources.oracle_knowledge.types import OracleKnowledgeConfig

logger = getLogger(__name__)
logger.setLevel("DEBUG")


class OracleKnowledgeDataSource(DataSource[dict]):
    def __init__(self, config: OracleKnowledgeConfig) -> None:
        logger.debug("Initialized OracleKnowledgeDataSource...")
        self.__url = config.url.rstrip("/") + "/"
        self.__auth = config.auth
        self.__limit = 20

    @property
    def name(self) -> str:
        return "Oracle Knowledge"

    @property
    def oracle_sharepoint_url(self) -> str:
        return self.__url

    async def get_data(self) -> list[dict]:
        logger.debug("get_data started")
        all_articles = []
        offset = 0

        async with httpx.AsyncClient() as client:
            while True:
                logger.debug(f"Fetching articles with offset {offset}")
                articles, has_more = await self.__get_content(client, offset)
                all_articles.extend(articles)
                logger.debug(f"Total articles fetched so far: {len(all_articles)}")

                if not has_more:
                    logger.debug("No more articles to fetch. Exiting loop.")
                    break

                # Update the offset for the next iteration
                offset += self.__limit

        logger.debug(f"Total articles fetched: {len(all_articles)}")
        return all_articles

    async def __get_content(
        self, client: httpx.AsyncClient, offset: int
    ) -> tuple[list[dict], bool]:
        logger.debug(f"__get_content started... offset {offset}")
        params = {
            "offset": offset,
            "limit": self.__limit,
            "q": "contentType.referenceKey eq 'FAQ'",
            "mode": "FULL",
        }

        try:
            url = f"{self.__url}/km/api/v1/content"
            logger.debug(f"Requesting data...{url}")
            response = await client.get(
                url,
                auth=self.__auth,
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            logger.debug(f"Response status: {response.status_code}")
            response_json = response.json()
            items = response_json.get("items", [])
            has_more = response_json.get("hasMore", False)

            logger.debug(f"Number of items fetched: {len(items)}")
            logger.debug(f"hasMore: {has_more}")
            logger.debug(f"offset {response_json.get('offset', -1)}")

            return items, has_more
        except httpx.RequestError as e:
            logger.error(f"An error occurred while fetching data: {e}")
            return [], False

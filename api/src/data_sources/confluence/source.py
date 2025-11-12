import asyncio

from atlassian import Confluence

from data_sources.confluence.types import ConfluencePage
from data_sources.data_source import DataSource


class ConfluenceDataSource(DataSource[ConfluencePage]):
    def __init__(self, confluence: Confluence, space_key: str) -> None:
        self.__confluence = confluence
        self.__space_key = space_key

    @property
    def name(self) -> str:
        return "Confluence"

    @property
    def instance_url(self) -> str:
        return self.__confluence.url

    async def get_data(self) -> list[ConfluencePage]:
        all_pages = await self.__get_all_confluence_pages()
        extended_pages = [
            await self.__prepend_root_page_name(page) for page in all_pages
        ]
        return extended_pages

    async def __get_all_confluence_pages(self) -> list[ConfluencePage]:
        start = 0
        limit = 100
        all_pages: list[ConfluencePage] = []

        while True:
            pages = await asyncio.to_thread(
                self.__confluence.get_all_pages_from_space,
                self.__space_key,
                start,
                limit,
                None,
                "history,version,body.storage",
                "page",
            )

            if not pages:
                break

            all_pages.extend([ConfluencePage.model_validate(page) for page in pages])
            start += limit

        return all_pages

    async def __get_root_page_name(self, page_id: str) -> str:
        ancestors = await asyncio.to_thread(
            self.__confluence.get_page_ancestors, page_id
        )

        # Filter ancestors with subType set
        ancestors = [ancestor for ancestor in ancestors if "subType" not in ancestor]

        if not ancestors:
            return ""

        rootPage = ancestors[0]
        return f"{rootPage.get('title')}___"

    async def __prepend_root_page_name(self, page: ConfluencePage) -> ConfluencePage:
        root_page_name = await self.__get_root_page_name(page.id)
        page.title = f"{root_page_name}{page.title}"
        return page

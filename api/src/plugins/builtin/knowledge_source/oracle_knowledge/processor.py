"""Oracle Knowledge Data Processor

This processor handles the transformation of Oracle Knowledge base articles into document chunks.
"""

import html
import re
import xml.etree.ElementTree as ET
from logging import getLogger

from data_sources.oracle_knowledge.source import OracleKnowledgeDataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from models import DocumentData

logger = getLogger(__name__)
logger.setLevel("DEBUG")


class OracleKnowledgeDataProcessor(DataProcessor):
    """Data processor for Oracle Knowledge base"""

    __items: list[dict]
    __data_source: OracleKnowledgeDataSource

    def __init__(self, data_source: OracleKnowledgeDataSource) -> None:
        logger.debug("OracleKnowledgeDataProcessor initializing")
        self.__data_source = data_source

    @property
    def data_source(self) -> OracleKnowledgeDataSource:
        return self.__data_source

    async def load_data(self) -> None:
        logger.debug("OracleKnowledgeDataProcessor load_data started")
        self.__items = await self.__data_source.get_data()

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        logger.debug(
            "OracleKnowledgeDataProcessor get_all_records_basic_metadata started",
        )
        return [
            SourceBasicMetadata(
                source_id=record.get("recordId", ""),
                title=record.get("title", ""),
                modified_date=record.get("dateModified", ""),
            )
            for record in self.__items
        ]

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        logger.debug(id)
        logger.debug("OracleKnowledgeDataProcessor create_chunks_from_doc started")

        item = next(
            (item for item in self.__items if str(item.get("recordId", "")) == id),
            None,
        )

        if not item:
            raise Exception(f"Item with id {id} not found")

        processed_record = self.__process_item(item)
        metadata = self.__create_base_metadata(item)
        return [self.__create_document(processed_record, metadata)]

    def __create_document(self, content: str, base_metadata: dict) -> DocumentData:
        if not content:
            raise ValueError("No content in __create_document")

        documents_data = DocumentData(content=content, metadata=base_metadata)

        return documents_data

    def __create_base_metadata(self, item: dict) -> dict:
        logger.debug("OracleKnowledgeDataProcessor __create_base_metadata started")
        logger.debug(item)
        docId = item.get("documentId", "")
        base_metadata = {
            "sourceId": item.get("recordId", ""),
            "versionId": item.get("recordId", ""),
            "documentId": item.get("documentId", ""),
            "version": item.get("version", ""),
            "answerId": item.get("answerId", ""),
            "source": f"{self.__data_source.oracle_sharepoint_url}fscmUI/faces/deeplink?objType=CSO_ARTICLE_CONTENT_KM&objKey=docId={docId};locale=en_US&action=EDIT_IN_TAB",
            "title": item.get("title", ""),
            "status": item.get("articleStatus", {}).get("name"),
            "createdTime": item.get("createDate", ""),
            "modifiedTime": item.get("dateModified", ""),
            "priority": item.get("priority", ""),
            "type": item.get("contentType", {}).get("name"),
        }
        logger.debug(base_metadata)
        return base_metadata

    def remove_html_tags(self, text: str):
        clean = re.sub("<[^<]+?>", "", text)
        clean = html.unescape(clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def __process_item(self, item: dict) -> str:
        logger.debug("OracleKnowledgeDataProcessor __process_record started")
        xml_content = item.get("xml")
        if not xml_content:
            raise ValueError("No xml content in __process_item")
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Error parsing XML content: {e}")
            return ""

        question_element = root.find("QUESTION")
        answer_element = root.find("ANSWER")

        question_text = ""
        answer_text = ""
        if question_element is not None and question_element.text:
            question_cdata = question_element.text
            question_text = self.remove_html_tags(question_cdata)
        else:
            logger.warning("No QUESTION element found in XML")

        if answer_element is not None and answer_element.text:
            answer_cdata = answer_element.text
            answer_text = self.remove_html_tags(answer_cdata)
        else:
            logger.warning("No ANSWER element found in XML")

        result = f"{question_text}\n\n{answer_text}"
        logger.debug(result)
        return result

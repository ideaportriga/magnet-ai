import httpx

from data_sources.data_source import DataSource
from data_sources.rightnow.types import Answer, AnswersResponse


class RightNowDataSource(DataSource[dict]):
    def __init__(self, url: str, auth: httpx.BasicAuth) -> None:
        self.__url = url
        self.__auth = auth

    @property
    def name(self) -> str:
        return "RightNow"

    @property
    def instance_url(self) -> str:
        return self.__url

    async def get_data(self) -> list[Answer]:
        answers = await self.__get_answers()

        return [answer for answer in answers if self.__is_answer_valid(answer)]

    def __is_answer_valid(self, answer: Answer) -> bool:
        return (
            answer.question is not None
            and answer.solution is not None
            and answer.summary is not None
        )

    async def __get_answers(self) -> list[Answer]:
        url = f"{self.__url}/services/rest/connect/v1.4/answers"
        headers = {"OSvC-CREST-Application-Context": "1"}
        params = {
            "fields": "question,solution,summary",
            "q": "statusWithType.status.lookupName='Public'",
        }

        auth = self.__auth
        async with httpx.AsyncClient(timeout=5000.0) as client:
            try:
                response = await client.get(
                    url=url,
                    auth=auth,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError:
                # Handle/log exception as needed
                raise

            answers_response = AnswersResponse.model_validate_json(response.text)
            answers = answers_response.items

            while answers_response.has_more:
                url = next(
                    (
                        link.href
                        for link in answers_response.links
                        if link.rel == "next"
                    ),
                    None,
                )
                if not url:
                    break

                response_json = await self.__get(url, headers)
                answers_response = AnswersResponse.model_validate_json(response_json)

                answers.extend(answers_response.items)

        return answers

    async def __get(self, url: str, headers: dict[str, str]) -> str:
        auth = self.__auth
        async with httpx.AsyncClient(timeout=5000.0) as client:
            try:
                response = await client.get(url=url, auth=auth, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError:
                # Handle/log exception as needed
                raise
            return response.text

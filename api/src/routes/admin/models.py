from logging import getLogger
from typing import Any

from litestar import post
from litestar.exceptions import ClientException, NotFoundException
from litestar.status_codes import (
    HTTP_204_NO_CONTENT,
)

from openai_model.utils import set_default_model

from .create_entity_controller import create_entity_controller

logger = getLogger(__name__)

ModelsBaseController = create_entity_controller(
    path_param="/models",
    collection_name="models",
)


class ModelsController(ModelsBaseController):
    tags = ["models"]

    @post("/set_default", status_code=HTTP_204_NO_CONTENT)
    async def set_default_handler(self, data: dict[str, Any]) -> None:
        """Set default model handler"""
        try:
            type_value = data.get("type")
            system_name = data.get("system_name")

            if not type_value or not system_name:
                raise ClientException("'type' and 'system_name' are required fields")

            await set_default_model(type_value, system_name)
            return

        except LookupError as e:
            logger.warning(str(e))
            raise NotFoundException(str(e))
        except Exception as err:
            logger.error(
                "Unexpected error occurred while setting default model: %s",
                err,
            )
            raise ClientException(
                "Unexpected error occurred while setting default model",
            )

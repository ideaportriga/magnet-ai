import json
from datetime import datetime
from typing import Annotated, Any

from litestar import Controller, Response, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT

from services.transfer import export_entities, import_entities


class TransferController(Controller):
    path = "/transfer"
    tags = ["Admin / Transfer"]

    @post("/export/json", status_code=HTTP_200_OK)
    async def export_json(
        self,
        data: dict[str, Any] | None = None,
        skip_chunks: bool = False,
    ) -> dict[str, Any]:
        """Export data as JSON response"""
        result = await export_entities(data or {}, skip_chunks)

        return result

    @post("/export/file", status_code=HTTP_200_OK)
    async def export_file(
        self,
        data: dict[str, Any] | None = None,
        skip_chunks: bool = False,
    ) -> Response[bytes]:
        """Export data as downloadable JSON file"""
        result = await export_entities(data or {}, skip_chunks)

        timestamp = datetime.now().strftime("%Y_%m-%d:%H:%M:%S")
        filename = f"data_transfer_{timestamp}.json"

        return Response(
            content=json.dumps(result).encode("utf-8"),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @post("/import/json", status_code=HTTP_204_NO_CONTENT)
    async def import_json(
        self,
        data: dict[str, Any],
    ) -> None:
        """Import data from JSON payload"""
        if not data:
            raise ClientException("No import data")

        await import_entities(data)

    @post("/import/file", status_code=HTTP_204_NO_CONTENT)
    async def import_file(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> None:
        """Import data from uploaded JSON file"""
        if not data:
            raise ClientException("No file uploaded")

        try:
            # TODO ASYNCMIGRATION - use await when the route handler is async
            file_content = await data.read()
            # file_content = data.file.read()
            import_data = json.loads(file_content)
        except json.JSONDecodeError:
            raise ClientException("Invalid JSON file")

        await import_entities(import_data)

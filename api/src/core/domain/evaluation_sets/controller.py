from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

import pandas as pd
from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.connection import Request
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body, Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.evaluation_sets.service import (
    EvaluationSetsService,
)
from guards.permissions import Permission, require_permission
from services.access_control import (
    attach_permissions,
    enforce_action_or_403,
    enforce_view_or_404,
    force_create_fields,
    visibility_filter_for,
)

from .schemas import EvaluationSet, EvaluationSetCreate, EvaluationSetUpdate

if TYPE_CHECKING:
    pass


_RESOURCE = "evaluations"


@dataclass
class FormData:
    json: str
    file: UploadFile | None = None


class EvaluationSetsController(Controller):
    """Evaluation Sets CRUD — tenant + record-level scoped (PR 10 rollout)."""

    path = "/evaluation_sets"
    tags = ["Admin / Evaluation Sets"]

    dependencies = providers.create_service_dependencies(
        EvaluationSetsService,
        "evaluation_sets_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
            "sort_field": "updated_at",
            "sort_order": "desc",
        },
    )

    @get(guards=[require_permission(Permission.EVALUATIONS_READ)])
    async def list_evaluation_sets(
        self,
        evaluation_sets_service: EvaluationSetsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[EvaluationSet]:
        """List evaluation sets — filtered by record-level visibility."""
        from core.db.models.evaluation_set.evaluation_set import (
            EvaluationSet as EvaluationSetModel,
        )

        extra_filters: list = list(filters)
        where = await visibility_filter_for(
            evaluation_sets_service,
            request=request,
            model=EvaluationSetModel,
            resource_type=_RESOURCE,
        )
        if where is not None:
            extra_filters.append(where)
        results, total = await evaluation_sets_service.list_and_count(*extra_filters)
        page = evaluation_sets_service.to_schema(
            results, total, filters=filters, schema_type=EvaluationSet
        )
        if request.scope.get("auth") is not None and page.items:
            for item, model in zip(page.items, results):
                await attach_permissions(
                    evaluation_sets_service,
                    item,
                    model,
                    request=request,
                    resource_type=_RESOURCE,
                )
        return page

    @post(guards=[require_permission(Permission.EVALUATIONS_WRITE)])
    async def create_evaluation_set(
        self,
        evaluation_sets_service: EvaluationSetsService,
        data: EvaluationSetCreate,
        request: Request,
        audit_username: str | None,
    ) -> EvaluationSet:
        """Create a new evaluation set. tenant_id + owner_id forced from auth."""
        from core.db.models.evaluation_set.evaluation_set import (
            EvaluationSet as EvaluationSetModel,
        )

        data.created_by = audit_username
        data.updated_by = audit_username
        payload = data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username
        obj = await evaluation_sets_service.create(
            EvaluationSetModel(**payload), auto_commit=True
        )
        schema = evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)
        return await attach_permissions(
            evaluation_sets_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @post("/file", guards=[require_permission(Permission.EVALUATIONS_WRITE)])
    async def create_evaluation_set_from_file(
        self,
        evaluation_sets_service: EvaluationSetsService,
        data: Annotated[FormData, Body(media_type=RequestEncodingType.MULTI_PART)],
        request: Request,
        audit_username: str | None,
    ) -> EvaluationSet:
        """Create a new evaluation set from file upload."""
        from core.db.models.evaluation_set.evaluation_set import (
            EvaluationSet as EvaluationSetModel,
        )

        json_data = json.loads(data.json)
        evaluation_set_data = EvaluationSetCreate(**json_data)
        evaluation_set_data.created_by = audit_username
        evaluation_set_data.updated_by = audit_username

        file = data.file
        if file:
            file_content = await file.read()
            excel_data = pd.read_excel(
                io.BytesIO(file_content),
                header=None,
                dtype=str,
            ).fillna("")

            items = []
            for index, row in excel_data.iterrows():
                user_input = row.get(0, "")
                expected_result = row.get(1, "")
                item = {
                    "user_input": user_input,
                    "expected_result": expected_result,
                }
                items.append(item)

            evaluation_set_data.items = items

        payload = evaluation_set_data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username
        obj = await evaluation_sets_service.create(
            EvaluationSetModel(**payload), auto_commit=True
        )
        schema = evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)
        return await attach_permissions(
            evaluation_sets_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @get(
        "/code/{code:str}",
        guards=[require_permission(Permission.EVALUATIONS_READ)],
    )
    async def get_evaluation_set_by_code(
        self,
        evaluation_sets_service: EvaluationSetsService,
        code: str,
        request: Request,
    ) -> EvaluationSet:
        """Get an evaluation set by its system_name."""
        obj = await evaluation_sets_service.get_one(system_name=code)
        await enforce_view_or_404(
            evaluation_sets_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)
        return await attach_permissions(
            evaluation_sets_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @get(
        "/{evaluation_set_id:uuid}",
        guards=[require_permission(Permission.EVALUATIONS_READ)],
    )
    async def get_evaluation_set(
        self,
        evaluation_sets_service: EvaluationSetsService,
        request: Request,
        evaluation_set_id: UUID = Parameter(
            title="Evaluation Set ID",
            description="The evaluation set to retrieve.",
        ),
    ) -> EvaluationSet:
        """Get an evaluation set by its ID. 404 if caller can't view it."""
        obj = await evaluation_sets_service.get(evaluation_set_id)
        await enforce_view_or_404(
            evaluation_sets_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)
        return await attach_permissions(
            evaluation_sets_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @patch(
        "/{evaluation_set_id:uuid}",
        guards=[require_permission(Permission.EVALUATIONS_WRITE)],
    )
    async def update_evaluation_set(
        self,
        evaluation_sets_service: EvaluationSetsService,
        data: EvaluationSetUpdate,
        request: Request,
        evaluation_set_id: UUID = Parameter(
            title="Evaluation Set ID",
            description="The evaluation set to update.",
        ),
        audit_username: str | None = None,
    ) -> EvaluationSet:
        """Update an evaluation set. 404/403 per record-level access rules."""
        existing = await evaluation_sets_service.get(evaluation_set_id)
        await enforce_action_or_403(
            evaluation_sets_service,
            request=request,
            action="edit",
            resource=existing,
            resource_type=_RESOURCE,
        )
        update_data = data.model_dump(exclude_unset=True)
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        update_data["updated_by"] = audit_username
        obj = await evaluation_sets_service.update(
            update_data, item_id=evaluation_set_id, auto_commit=True
        )
        schema = evaluation_sets_service.to_schema(obj, schema_type=EvaluationSet)
        return await attach_permissions(
            evaluation_sets_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @delete(
        "/{evaluation_set_id:uuid}",
        guards=[require_permission(Permission.EVALUATIONS_WRITE)],
    )
    async def delete_evaluation_set(
        self,
        evaluation_sets_service: EvaluationSetsService,
        request: Request,
        evaluation_set_id: UUID = Parameter(
            title="Evaluation Set ID",
            description="The evaluation set to delete.",
        ),
    ) -> None:
        """Delete an evaluation set. 404/403 per record-level access rules."""
        existing = await evaluation_sets_service.get(evaluation_set_id)
        await enforce_action_or_403(
            evaluation_sets_service,
            request=request,
            action="delete",
            resource=existing,
            resource_type=_RESOURCE,
        )
        await evaluation_sets_service.delete(evaluation_set_id)

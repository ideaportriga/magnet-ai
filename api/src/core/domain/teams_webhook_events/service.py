from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.teams.teams_webhook_event import TeamsWebhookEvent


class TeamsWebhookEventsService(
    service.SQLAlchemyAsyncRepositoryService[TeamsWebhookEvent]
):
    """Receipt-of-delivery for Microsoft Graph webhook notifications.

    Used by the webhook handler to deduplicate at-least-once deliveries from
    Graph and to durably stage the original notification payload before a
    worker picks it up — see `services/agents/teams/webhook_intake.py`.
    """

    class Repo(repository.SQLAlchemyAsyncRepository[TeamsWebhookEvent]):
        model_type = TeamsWebhookEvent

    repository_type = Repo

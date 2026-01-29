from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from .state import NoteTakerHandlerState


def register(app: AgentApplication[TurnState], state: NoteTakerHandlerState) -> None:
    @app.on_sign_in_success
    async def _on_sign_in_success(
        context: TurnContext,
        turn_state: TurnState,
        handler_id: str | None = None,
    ) -> None:
        await state.on_sign_in_success(context, turn_state, handler_id=handler_id)

    @app.on_sign_in_failure
    async def _on_sign_in_failure(
        context: TurnContext,
        turn_state: TurnState,
        handler_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        await state.on_sign_in_failure(
            context,
            turn_state,
            handler_id=handler_id,
            error_message=error_message,
        )

    @app.activity("installationUpdate")
    async def _on_installation_update(
        context: TurnContext, turn_state: TurnState
    ) -> None:
        await state.on_installation_update(context, turn_state)

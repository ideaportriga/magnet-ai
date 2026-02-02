from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from .state import NoteTakerHandlerState


def register(app: AgentApplication[TurnState], state: NoteTakerHandlerState) -> None:
    @app.activity("message")
    async def _on_message(context: TurnContext, turn_state: TurnState) -> None:
        await state.on_message(context, turn_state)

from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from .state import NoteTakerHandlerState


def register(app: AgentApplication[TurnState], state: NoteTakerHandlerState) -> None:
    @app.activity("event")
    async def _on_event(context: TurnContext, turn_state: TurnState) -> None:
        await state.on_event(context, turn_state)

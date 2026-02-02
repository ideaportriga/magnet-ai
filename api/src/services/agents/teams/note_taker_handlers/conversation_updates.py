from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from .state import NoteTakerHandlerState


def register(app: AgentApplication[TurnState], state: NoteTakerHandlerState) -> None:
    @app.conversation_update("membersAdded")
    async def _on_members_added(context: TurnContext, turn_state: TurnState) -> None:
        await state.on_members_added(context, turn_state)

    @app.conversation_update("membersRemoved")
    async def _on_members_removed(context: TurnContext, turn_state: TurnState) -> None:
        await state.on_members_removed(context, turn_state)

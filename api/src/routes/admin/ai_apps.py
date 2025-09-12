from .create_entity_controller import create_entity_controller

AiAppsController = create_entity_controller(
    path_param="/ai_apps",
    collection_name="ai_apps",
    tags_param=["ai_apps"],
)

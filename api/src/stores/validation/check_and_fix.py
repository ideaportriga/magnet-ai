from logging import getLogger

logger = getLogger(__name__)


def run_check_and_fix(fix=False):
    logger.info("Running check and fix")

    checks = [
        check_assistant,
    ]

    results = []

    for check_func in checks:
        try:
            result = check_func(fix)
            results.append(result)
        except Exception as e:
            error_message = f"Error during {check_func.__name__}: {e}"
            logger.error(f"❌ {error_message}")
            results.append([False, error_message])

    logger.info("Results:")
    for result in results:
        if result[0]:
            logger.info(f"✅ {result[1]}")
        else:
            logger.error(f"❌ {result[1]}")

    return results


def check_assistant(fix=False):
    from stores import get_db_client

    client = get_db_client()
    if not client.get_collection("assistants").find_one(
        {"system_name": "SUPPORT_ASSISTANT"}
    ):
        if fix:
            client.get_collection("assistants").insert_one(
                {
                    "system_name": "SUPPORT_ASSISTANT",
                    "case_update_prompt_system_name": "CASE_UPDATE_PROMPT",
                    "tool_calling_prompt_system_name": "ASSISTANT_PROMPT",
                    "recommended_message_prompt_system_name": "ASSISTANT_RECOMMENDED_MESSAGE_PROMPT",
                },
            )
            return [True, "Fixed assistant"]
        return [False, "Assistant not found"]
    return [True, "Assistant found"]

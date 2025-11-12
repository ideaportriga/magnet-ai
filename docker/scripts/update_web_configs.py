import os
import json

ADMIN_CONFIG = "/app/web/admin/config/main.json"
PANEL_CONFIG = "/app/web/panel/config/main.json"

def build_config():
    config = {
        "auth": {
            "enabled": str(os.getenv("AUTH_ENABLED", "true")).lower() == "true",
        },
        "api": {"aiBridge": {"baseUrl": ""}},
        "panel": {"baseUrl": "/panel/"},
        "admin": {"baseUrl": "/admin/"},
    }

    if config["auth"]["enabled"]:
        config["auth"]["provider"] = os.getenv("WEB_AUTH_PROVIDER_TITLE", "Microsoft")
        config["auth"]["popup"] = {
            "width": int(os.getenv("WEB_AUTH_POPUP_WIDTH", "600")),
            "height": int(os.getenv("WEB_AUTH_POPUP_HEIGHT", "400")),
        }

    return config


def write_config(path, config):
    with open(path, "w") as file:
        json.dump(config, file, indent=2)

def main():
    config = build_config()

    write_config(ADMIN_CONFIG, config)
    write_config(PANEL_CONFIG, config)

if __name__ == "__main__":
    main()

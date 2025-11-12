#!/bin/sh
set -e

CONFIG_FILE="/usr/share/nginx/html/config/main.json"

# Mapping of CONFIG_* variables to JSON paths
CONFIG_MAP="CONFIG_ENVIRONMENT:environment
CONFIG_AUTH_ENABLED:auth.enabled
CONFIG_AUTH_PROVIDER:auth.provider
CONFIG_API_AIBRIDGE_BASEURL:api.aiBridge.baseUrl
CONFIG_API_AGENTS_BASEURL:api.agents.baseUrl
CONFIG_API_SALESFORCE_BASEURL:api.salesforce.baseUrl
CONFIG_THEME:theme
CONFIG_AUTH_POPUP_WIDTH:auth.popup.width
CONFIG_AUTH_POPUP_HEIGHT:auth.popup.height
CONFIG_PANEL_BASEURL:panel.baseUrl
CONFIG_ADMIN_BASEURL:admin.baseUrl"

# Function to update JSON value
update_json_value() {
    key=$1
    value=$2
    file=$3
    
    # Use temp file to handle in-place editing
    tmp=$(mktemp)
    
    # Split the key into an array and use setpath
    jq --arg key "$key" --arg value "$value" \
    'def split_path: $key | split("."); setpath(split_path; $value)' \
    "$file" > "$tmp" && mv "$tmp" "$file" && chmod 755 "$file"
}

# Process environment variables starting with CONFIG_
for var in $(env | grep ^CONFIG_); do
    # Split env var into key and value
    key=$(echo "$var" | cut -d= -f1)
    value=$(echo "$var" | cut -d= -f2-)
    
    # Check if the key is in the CONFIG_MAP
    json_path=$(echo "$CONFIG_MAP" | grep "^${key}:" | cut -d: -f2)

    if [ -n "$json_path" ]; then
        # Update the JSON config file
        update_json_value "$json_path" "$value" "$CONFIG_FILE"
    fi
done


# Build MagnetAI docs
# We are building docs here, because we do know the base url of the docs at build time in the main CI/CD pipeline.
echo "Building documentation..."
cd /app/docs
yarn install
yarn vitepress build
cp -r .vitepress/dist /usr/share/nginx/html/help

# Execute CMD
exec "$@"
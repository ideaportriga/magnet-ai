# Slack Agent Installation

## Overview

This guide explains how to connect a Magnet AI agent to Slack. The integration receives events, slash commands, and interactive payloads, then delivers Magnet AI responses back to direct messages.

All URLs in this document are relative to your AI Bridge instance. Replace `{AI_BRIDGE_BASE}` with that origin when configuring external systems.

## Capabilities

- Responds to direct messages and mentions.
- Supports slash commands for welcome, restart, and conversation info. Take into account that Slack slash commands aren’t namespaced per app. If multiple apps in the same workspace register the same trigger, Slack will route the command to the app that was installed most recently—everywhere, including DMs with other apps. Magnet AI sample code handles command started with /welcome, /restart, and /get_conversation_info.
- Sends confirmation cards for actions that require approval.
- Collects Like/Dislike feedback (with reason and optional comments) and syncs it to Magnet AI.

## Prerequisites

- An existing Magnet AI agent.
- Slack workspace administrator rights to create and install custom apps.
- An externally reachable AI Bridge deployment (`https://{AI_BRIDGE_BASE}`).

## Step 1 – Update the Slack app

1. On [api.slack.com/apps](https://api.slack.com/apps), create or open your Slack app.
2. Under **Basic Information**, copy the **Client ID**, **Client Secret**, and **Signing Secret**.
3. In **OAuth & Permissions**, add a redirect URL: `https://{AI_BRIDGE_BASE}/api/user/agents/slack/oauth_redirect`, and list the Slack App scopes you need (for example `app_mentions:read, channels:history, chat:write, commands, im:history, mpim:history, users:read`).
4. In **Event Subscriptions**, set the request URL to `https://{AI_BRIDGE_BASE}/api/user/agents/slack/events` and subscribe to the channel or DM events required by your rollout.
5. Under **Interactivity & Shortcuts**, enable interactivity and reuse the same request URL.
6. Create the slash commands you intend to offer (`/welcome`, `/restart`, `/get_conversation_info`), each pointing to the same request URL.

## Step 2 – Configure the agent in Magnet AI

1. In the Magnet admin UI, open **Agents → {your agent} → Channels**.
2. Enable **Slack**.
3. Populate the fields:
   - **Client ID** – Slack app client ID.
   - **Client Secret** – Slack app client secret.
   - **Signing Secret** – Slack app signing secret.
   - **Agent Scopes** – Comma-separated list of scopes defined in Slack manifest.
   - **Token** – Optional Slack App token (`xoxb-…`) if you do not use OAuth, and in this scenario **Client Secret**, **Signing Secret**, and **Agent Scopes** are not needed.
4. Click **Save** to persist the changes. Secrets and Token are stored encrypted.
5. If you use OAuth, click **Connect to Slack** and complete the OAuth consent dialog to store the installation.

## Verification & Testing

1. Send welcome command to confirm the welcome message appears.
2. Ask the agent in DM or mention it in a channel, and verify it replies in place.
3. Trigger an action requiring confirmation and test both button responses.
4. Submit Like/Dislike feedback and confirm the Slack message updates accordingly.

## Example of Slack Application Manifest

```json
{
  "display_information": {
    "name": "Magnet Agent",
    "description": "Simple Slack App to send the user message to the Magnet AI Agent and return the answer",
    "background_color": "#6480c2"
  },
  "features": {
    "bot_user": {
      "display_name": "Magnet Agent",
      "always_online": false
    },
    "slash_commands": [
      {
        "command": "/restart",
        "url": "https://{AI_BRIDGE_BASE}/api/user/agents/slack/events",
        "description": "Starts the new conversation",
        "should_escape": false
      },
      {
        "command": "/welcome",
        "url": "https://{AI_BRIDGE_BASE}/api/user/agents/slack/events",
        "description": "Sends the welcome card",
        "should_escape": false
      },
      {
        "command": "/get_conversation_info",
        "url": "https://{AI_BRIDGE_BASE}/api/user/agents/slack/events",
        "description": "Returns the conversation info from Magnet",
        "should_escape": false
      }
    ]
  },
  "oauth_config": {
    "redirect_urls": ["https://{AI_BRIDGE_BASE}/api/user/agents/slack/oauth_redirect"],
    "scopes": {
      "bot": ["chat:write", "im:history", "im:read", "im:write", "users:read", "app_mentions:read", "commands"]
    }
  },
  "settings": {
    "event_subscriptions": {
      "request_url": "https://{AI_BRIDGE_BASE}/api/user/agents/slack/events",
      "bot_events": ["app_mention", "message.im"]
    },
    "interactivity": {
      "is_enabled": true,
      "request_url": "https://{AI_BRIDGE_BASE}/api/user/agents/slack/events"
    },
    "org_deploy_enabled": false,
    "socket_mode_enabled": false,
    "token_rotation_enabled": true
  }
}
```

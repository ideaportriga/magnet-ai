# Microsoft Teams Agent Installation

## Overview

This guide explains how to connect a Magnet AI Agent to Microsoft Teams. A Teams-enabled agent listens to conversations through the Azure Bot Service messaging endpoint, sends adaptive-card responses, and keeps feedback in sync with Magnet AI.

All URLs in this document are relative to your AI Bridge instance. Replace `{AI_BRIDGE_BASE}` with that origin when configuring external systems.

## Capabilities

- Sends adaptive-card replies.
- Supports commands typed by the user: `/welcome` to get welcome message, `/restart` to start the new conversation in Magnet AI, and `/get_conversation_info`.
- Presents action confirmations with **Confirm**/**Reject** buttons when needed.
- Collects message feedback (Like/Dislike with reason and optional comment).
- Sends a typing indicator while Magnet AI prepares the response.
- No group chats supported.

## Prerequisites

- An existing Magnet AI agent.
- An Azure tenant with **Azure Bot Service** configured.
- A packaged Microsoft Teams App already uploaded to Teams Admin Center.
- An externally reachable AI Bridge deployment (`https://{AI_BRIDGE_BASE}`).

## Step 1 – Update the Azure Bot Service

1. Under **Configuration**, set the **Messaging endpoint** to:

   ```
   https://{AI_BRIDGE_BASE}/api/user/agents/teams/messages
   ```

2. Record these values:
   - **Microsoft App ID** → becomes the Magnet **Client ID**.
   - **Tenant ID** from the linked Azure AD app registration.
   - A new **Client secret** (under App Registration → Certificates & secrets → New client secret). Copy the secret value immediately; Azure hides it after you leave the page.

## Step 2 – Configure the agent in Magnet AI

1. Navigate to **Agents → {your agent} → Channels** in the Magnet admin panel.
2. Enable **Ms Teams**.
3. Populate the fields:
   - **Client ID** – Microsoft App ID from Azure Bot Service.
   - **Tenant ID** – Tenant ID associated with the Azure Bot Service.
   - **Secret value** – the client secret you created for App Registration used by Azure Bot Service.
4. Click **Save** to persist the changes. The secret value is encrypted at rest.

## Verification & Testing

1. Send `/welcome` to verify the welcome adaptive card renders.
2. Ask a question the agent can answer; confirm that a response card is displayed and that feedback buttons work.

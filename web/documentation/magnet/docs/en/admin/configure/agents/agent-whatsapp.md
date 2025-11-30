# WhatsApp Agent Installation

## Overview

This guide explains how to connect a Magnet AI agent to the WhatsApp Business Platform. Magnet validates Meta webhook signatures with your app secret and uses the WhatsApp Graph API to send replies back to end users.

All Magnet endpoints in this document are relative to your AI Bridge instance. Replace `{AI_BRIDGE_BASE}` with that origin when configuring external systems.

## Capabilities

- Delivers Magnet AI responses to WhatsApp conversations.
- Supports commands typed by the user: `/welcome` to get welcome message, `/restart` to start the new conversation in Magnet AI, and `/get_conversation_info`.
- Presents confirmation buttons (✅ Confirm / ✋ Reject) when actions need approval.
- Collects Like/Dislike feedback and syncs it to Magnet AI.
- No group chats supported.

## Prerequisites

- An existing Magnet AI agent.
- A WhatsApp Business Platform app with a verified phone number.
- WhatsApp Business Account permissions to manage webhooks.
- The Meta app secret for your WhatsApp application.
- An externally reachable AI Bridge deployment (`https://{AI_BRIDGE_BASE}`).

## Step 1 – Update the WhatsApp app

1. In [developers.facebook.com](https://developers.facebook.com/), open your WhatsApp app and note the **Phone Number ID** shown under **WhatsApp > API Setup**.
2. Generate a permanent access token (System Users → Assign Assets → WhatsApp Business API → Generate Token) with the required scopes and store it securely.
3. Copy the **App Secret** from **App Settings > Basic**.
4. Under **WhatsApp > Configuration**, set the callback URL to `https://{AI_BRIDGE_BASE}/api/user/agents/whatsapp/messages` and provide any verify token of your choice (could be any).
5. Click **Verify and Save** so Meta can confirm ownership, then subscribe to the `messages` webhook field (and any additional fields you need if you need).

## Step 2 – Configure the agent in Magnet AI

1. In the Magnet admin UI, open **Agents → {your agent} → Channels**.
2. Enable **WhatsApp**.
3. Populate the fields:
   - **Phone Number ID** – Value from WhatsApp API Setup.
   - **Token** – Permanent access token with the required scopes.
   - **App Secret** – Meta app secret used for signature validation.
4. Save the agent configuration. The token and app secret are stored encrypted.

## Verification & Testing

1. Send `welcome` (or `/welcome`) from a registered phone to confirm the welcome message is returned.
2. Ask a question the agent can answer and verify that the response arrives in WhatsApp.
3. Trigger an action that requires confirmation and test both Confirm and Reject buttons.
4. Submit Like or Dislike feedback and confirm the acknowledgement is sent.

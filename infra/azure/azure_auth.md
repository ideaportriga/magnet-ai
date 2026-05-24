# Magnet-AI: Microsoft Entra ID Authentication Setup

Instructions for the Azure administrator to enable authentication on the **magnet-ai** Container App (`ca-magnet-ai-{env}`).

> **Context:** the Bicep/ARM template in this folder deploys the Container App with authentication disabled by default (see the *Authentication* section in [`README.md`](README.md)). Until the steps below are completed and `AUTH_ENABLED=true`, the app is publicly reachable with no sign-in required — set `ingressAllowedIpRange` at deploy time to restrict ingress to a known public IP while this setup is in progress.

---

## 1. Create an App Registration

1. Go to **Azure Portal > Microsoft Entra ID > App registrations > New registration**
2. Fill in:
   - **Name:** `Magnet AI` (or `Magnet AI - Dev` / `Magnet AI - Prod` per environment)
   - **Supported account types:** *Accounts in this organizational directory only* (single tenant)
   - **Redirect URI:** Select **Web** and enter:
     ```
     https://ca-magnet-ai-{env}.{defaultDomain}/auth/callback
     ```
     Replace `{env}` with the environment name (e.g. `dev`) and `{defaultDomain}` with the Container App Environment's default domain (visible in Azure Portal under the Container App Environment resource, or in the Bicep deployment outputs).
     
     Example: `https://ca-magnet-ai-dev.niceocean-abcd1234.swedencentral.azurecontainerapps.io/auth/callback`
3. Click **Register**

After creation, note down:
- **Application (client) ID** — shown on the Overview page
- **Directory (tenant) ID** — shown on the Overview page

## 2. Create a Client Secret

1. In the App Registration, go to **Certificates & secrets > Client secrets > New client secret**
2. Add a description (e.g. `magnet-ai-prod`) and choose an expiry period
3. Click **Add**
4. **Copy the secret Value immediately** — it is only shown once

## 3. Configure API Permissions

1. In the App Registration, go to **API permissions**
2. Verify the following **Microsoft Graph** delegated permissions are present (they should be added by default):
   - `openid`
   - `profile`
   - `email`
3. If any are missing, click **Add a permission > Microsoft Graph > Delegated permissions** and add them

4. Click **Grant admin consent for {your tenant}** if required by your organization's policies

## 4. Define an Admin App Role

1. In the App Registration, go to **App roles > Create app role**
2. Fill in:
   - **Display name:** `Admin`
   - **Allowed member types:** *Users/Groups*
   - **Value:** `admin`
   - **Description:** `Full access to Magnet AI`
   - **Enable this app role:** checked
3. Click **Apply**

## 5. Assign Users or Groups to the App Role

1. Go to **Azure Portal > Microsoft Entra ID > Enterprise applications**
2. Find the application created in step 1 (search by name or client ID)
3. Go to **Users and groups > Add user/group**
4. Select the users or security group that should have access
5. Select the **admin** role
6. Click **Assign**

> **Tip:** Create a security group (e.g. `Magnet AI Users`) and assign the role to the group.
> Then manage access by adding/removing members from the group instead of editing role assignments directly.

## 6. (Optional) Restrict Access to Assigned Users Only

To ensure **only** users with an assigned role can sign in:

1. In **Enterprise applications**, select the Magnet AI app
2. Go to **Properties**
3. Set **Assignment required?** to **Yes**
4. Click **Save**

With this enabled, users without an assigned role will get an error when trying to sign in.

## 7. Set Environment Variables on the Container App

The app is already deployed. The following secrets and environment variables need to be added to the `ca-magnet-ai-{env}` Container App.

### Variables to Set

| Container Env Variable                | Value                                              | Type   |
|---------------------------------------|----------------------------------------------------|--------|
| `AUTH_ENABLED`                        | `true`                                             | Plain  |
| `MICROSOFT_ENTRA_ID_CLIENT_ID`       | Application (client) ID from step 1                | Secret |
| `MICROSOFT_ENTRA_ID_CLIENT_SECRET`   | Client secret Value from step 2                    | Secret |
| `MICROSOFT_ENTRA_ID_TENANT_ID`       | Directory (tenant) ID from step 1                  | Plain  |
---

### Option A: Azure Portal

1. Go to **Azure Portal > Container Apps > `ca-magnet-ai-{env}`**

**Add secrets first** (secrets must exist before they can be referenced by env vars):

2. Go to **Security > Secrets**
3. Click **Add** for each secret:
   - **Name:** `entra-client-id`, **Value:** `<Application (client) ID>`
   - **Name:** `entra-client-secret`, **Value:** `<Client Secret Value>`

**Then add environment variables:**

4. Go to **Application > Containers** and click **Edit and deploy**
5. Click on the container (`ca-magnet-ai-{env}`) to edit it
6. Under **Environment variables**, add:
   - `AUTH_ENABLED` = `true` (Source: **Manual entry**)
   - `MICROSOFT_ENTRA_ID_TENANT_ID` = `<Directory (tenant) ID>` (Source: **Manual entry**)
   - `MICROSOFT_ENTRA_ID_CLIENT_ID` — (Source: **Reference a secret**, select `entra-client-id`)
   - `MICROSOFT_ENTRA_ID_CLIENT_SECRET` — (Source: **Reference a secret**, select `entra-client-secret`)
7. Click **Save as a new revision**

---

### Option B: Azure CLI

```bash
# Step 1: Add secrets
az containerapp secret set \
  --name ca-magnet-ai-{env} \
  --resource-group rg-magnet-ai-{env} \
  --secrets \
    entra-client-id="<Application (client) ID>" \
    entra-client-secret="<Client Secret Value>"

# Step 2: Set environment variables (plain values + secret references)
az containerapp update \
  --name ca-magnet-ai-{env} \
  --resource-group rg-magnet-ai-{env} \
  --set-env-vars \
    AUTH_ENABLED=true \
    MICROSOFT_ENTRA_ID_TENANT_ID="<Directory (tenant) ID>" \
    MICROSOFT_ENTRA_ID_CLIENT_ID=secretref:entra-client-id \
    MICROSOFT_ENTRA_ID_CLIENT_SECRET=secretref:entra-client-secret
```

> **Note:** The `secretref:` prefix tells Azure Container Apps to reference a secret by name rather than setting a plain-text value. Secrets must be created (step 1) before they can be referenced (step 2).

## 8. Verify

1. Open the app URL: `https://ca-magnet-ai-{env}.{defaultDomain}`
2. You should be redirected to the Microsoft login page
3. Sign in with a user that has been assigned the admin role
4. On success, you should be redirected back to the application

## Summary Checklist

- [ ] App Registration created (single tenant, Web platform)
- [ ] Redirect URI set to `https://ca-magnet-ai-{env}.{defaultDomain}/auth/callback`
- [ ] Client secret created and value copied
- [ ] API permissions granted: `openid`, `profile`, `email`
- [ ] App Role `Admin` created
- [ ] Users/groups assigned to the Admin role
- [ ] "Assignment required" set to Yes (optional, recommended)
- [ ] Secrets `entra-client-id` and `entra-client-secret` added to the Container App
- [ ] Environment variables set on the container (`AUTH_ENABLED`, `MICROSOFT_ENTRA_ID_*`)

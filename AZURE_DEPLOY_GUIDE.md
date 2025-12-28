# Deploying AI-Vidya to Microsoft Azure App Service

Since you have Azure credits, deploying to **Azure App Service** is an excellent choice. It makes your app scalable, secure, and professional.

## Phase 1: Create the Web App in Azure Portal

1.  Log in to the [Azure Portal](https://portal.azure.com).
2.  Search for **"App Services"** in the top search bar and select it.
3.  Click **+ Create** -> **Web App**.
4.  **Basics Tab**:
    *   **Subscription**: Select your subscription with credits.
    *   **Resource Group**: Create new (e.g., `rg-ai-vidya`).
    *   **Name**: Unique name (e.g., `ai-vidya-app`).
    *   **Publish**: `Code`.
    *   **Runtime stack**: `Python 3.9` (or 3.10/3.11, whichever matches you locally).
    *   **Operating System**: `Linux`.
    *   **Region**: Select a region close to you (e.g., `Central India`, `East US`).
    *   **Pricing Plan**: Select a plan. If you have credits, **Basic B1** or **Standard S1** are good. For free testing, **Free F1**.
    *   Click **Review + create** -> **Create**.

## Phase 2: Connect GitHub Repository

1.  Once deployment is complete, click **Go to resource**.
2.  In the left menu, under **Deployment**, click **Deployment Center**.
3.  **Settings**:
    *   **Source**: `GitHub`.
    *   **Signed in as**: Authorize your GitHub account.
    *   **Organization**: Select your username (`ayush6645`).
    *   **Repository**: `AI-vidya`.
    *   **Branch**: `main`.
4.  Click **Save**.
   *(Azure will now create a GitHub Action workflow in your repo and start building).*

## Phase 3: Configure Environment Variables

Azure needs your secrets (like the Google API key and Firebase credentials) to run the app.

1.  In the App Service menu (left side), under **Settings**, click **Environment variables** (sometimes under "Configuration").
2.  Click **+ Add** for each variable below:

    | Name | Value |
    | :--- | :--- |
    | `FLASK_SECRET_KEY` | `(Make up a long random string)` |
    | `GOOGLE_API_KEY` | `(Your Gemini API Key)` |
    | `YOUTUBE_API_KEY` | `(Your YouTube Data API Key)` |
    | `FIREBASE_CREDENTIALS` | `(Paste the FULL content of your serviceAccountKey.json)` |

    *Note: For `FIREBASE_CREDENTIALS`, copy the entire JSON content from your local `serviceAccountKey.json` file. Azure handles the JSON structure fine.*

3.  Click **Apply** -> **Confirm** (or **Save** at the top).

## Phase 4: Configure Startup Command

To ensure the app starts correctly with Gunicorn:

1.  In the App Service menu, under **Settings**, click **Configuration**.
2.  Go to the **General settings** tab.
3.  In the **Startup Command** field, enter:
    ```bash
    gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app
    ```
    *(Or simply `sh startup.sh` since we created that file for you)*.
4.  Click **Save**.

## Phase 5: Verify

1.  Go to the **Overview** blade.
2.  Click the **Default domain** URL (e.g., `https://ai-vidya-app.azurewebsites.net`).
3.  Your app should load!

---
### Troubleshooting
- **Application Error :** Check **Log Stream** in the left menu.
- **Module Not Found:** Ensure `requirements.txt` is updated (I have already done this).
- **500 Error:** Check that `FIREBASE_CREDENTIALS` is pasted correctly.

# How to Deploy AI-Vidya Safely

Your project is now securely pushed to GitHub. All sensitive keys (API keys, Service Accounts) have been removed from the code history to prevent hacking.

## option 1: Deploy to Google App Engine (Recommended since you use Google Cloud)

Since you already have `app.yaml`, this is the most native path.

1.  **Open Terminal** in this folder.
2.  **Login to Google Cloud**:
    ```bash
    gcloud auth login
    gcloud config set project YOUR_PROJECT_ID
    ```
3.  **Deploy**:
    ```bash
    gcloud app deploy
    ```
    *Note: Google App Engine uses `app.yaml`. Ensure your keys in `app.yaml` are correct before deploying (but DO NOT commit them to git).*

## Option 2: Deploy to Render (Free/Easy)

1.  Go to [Render.com](https://render.com) and create an account.
2.  Click **New +** -> **Web Service**.
3.  Connect your GitHub repository (`ayush6645/AI-vidya`).
4.  **Settings**:
    *   **Runtime**: Python 3
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn app:app`
5.  **Environment Variables** (CRITICALLY IMPORTANT):
    You must add these in the "Environment" tab on Render:
    *   `GOOGLE_API_KEY`: (Your Gemini Key)
    *   `YOUTUBE_API_KEY`: (Your YouTube Key)
    *   `FLASK_SECRET_KEY`: (A random string)
    *   `FIREBASE_CREDENTIALS`: (See below)

    *Since you use a `serviceAccountKey.json` file, on specific platforms like Render, you often need to paste the CONTENT of that file into a variable, or use a "Secret File" upload if they support it.*

## What was updated?
- **Security**: Removed `serviceAccountKey.json`, `.env`, and `app.yaml` from GitHub history.
- **Model**: Updated code to use `gemini-2.5-flash`.
- **Config**: Added `.env.example` and `app.yaml.example` for reference.

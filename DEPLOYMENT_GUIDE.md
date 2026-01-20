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

## Option 3: Deploy to Google Cloud Run (Modern/Scalable)

1. **Build and Submit to Container Registry**:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-vidya
   ```
2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy ai-vidya \
     --image gcr.io/YOUR_PROJECT_ID/ai-vidya \
     --platform managed \
     --region YOUR_REGION \
     --allow-unauthenticated \
     --set-env-vars "GOOGLE_API_KEY=your_key,YOUTUBE_API_KEY=your_key,FIREBASE_CREDENTIALS='{...content of json...}'"
   ```

*Important: For `FIREBASE_CREDENTIALS`, copy the ENTIRE content of your `serviceAccountKey.json` and paste it as a single-quoted string.*

## Troubleshooting "Container Doesn't Start"
If you see "Container doesn't start or listen on port":
- Ensure you have set the `FIREBASE_CREDENTIALS` environment variable.
- In Cloud Run, the port is handled automatically via the `$PORT` variable (now correctly configured in the `Dockerfile`).
- Check Cloud Logging for "FATAL" or "ERROR" messages during startup.

## What was updated?
- **Security**: Removed `serviceAccountKey.json`, `.env`, and `app.yaml` from GitHub history.
- **Model**: Updated code to use `gemini-2.0-flash`.
- **Infrastructure**: Added `Dockerfile` and `gunicorn` for production-grade deployment on Cloud Run.

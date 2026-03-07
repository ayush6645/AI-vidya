# AI Edu Bot - Mobile App

This is the Flutter mobile application for AI Edu Bot.

## Prerequisites

- [Flutter SDK](https://flutter.dev/docs/get-started/install) installed and in your PATH.
- Android Studio / Xcode for native build tools.

## Setup

1.  **Initialize the project:**
    Since the files were generated manually, you might need to run:
    ```bash
    flutter create .
    ```
    This will generate the `android/`, `ios/`, and `web/` folders that are not included in the source control.

2.  **Install dependencies:**
    ```bash
    flutter pub get
    ```

## Running the App

1.  **Run Flutter:**
    ```bash
    flutter run
    ```
    - **Backend:** Connected to `https://ai-vidya-990444310222.asia-south1.run.app`
    - To switch back to local dev, edit `lib/services/api_service.dart`.

## Features implemented

- **Authentication:** Login and Register with backend API integration.
- **Dashboard:** UI ported from Web App with glassmorphism design.
- **Theme:** Dark mode with custom colors.

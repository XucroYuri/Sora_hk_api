<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# CineFlow Console (Frontend)

This app connects to the CineFlow FastAPI backend and provides the admin console UI.

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Configure API base (optional, defaults to `http://127.0.0.1:8088/api/v1`):
   `VITE_API_BASE=http://127.0.0.1:8088/api/v1`
3. If backend auth is enabled, set:
   `VITE_AUTH_TOKEN=your_token`
4. Run the app:
   `npm run dev`

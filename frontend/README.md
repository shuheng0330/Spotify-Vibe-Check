# Spotify Vibe Check Frontend

React/Vite frontend for the Spotify Vibe Check FastAPI backend.

The frontend renders the same core information that previously lived in Streamlit: DJ chat, active playlist preview, t-SNE cluster exploration, top artists, representative tracks, audio-feature distributions, model comparison, diagnostic plots, cohesion/separation metrics, generated academic report text, and saved playlists.

## Run Locally

1. Install dependencies:

```bash
npm install
```

2. Copy environment values:

```bash
copy .env.example .env.local
```

3. Start the FastAPI backend from the project root:

```bash
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --reload --port 8000
```

4. Start the frontend:

```bash
npm run dev
```

The frontend expects `VITE_API_BASE_URL=http://localhost:8000`.

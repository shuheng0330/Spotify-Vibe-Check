# Spotify Vibe Check

Spotify Vibe Check is a React + FastAPI music exploration app that combines unsupervised audio-feature clustering with a conversational DJ assistant.

The app groups tracks by acoustic profile, then lets users describe a mood or listening context in natural language. A Dynamic DJ agent interprets the request, selects the best matching cluster, and returns a playlist built from that cluster.

---

## What this project does

- Loads a lecturer-approved Kaggle Spotify tracks dataset from `data/raw/spotify_kaggle.csv`.
- Normalizes supported Kaggle schemas into the app's internal track schema.
- Preprocesses and scales audio features, including outlier flags.
- Reduces dimensionality with PCA, then compares KMeans, GMM, and DBSCAN.
- Selects the production clustering model from KMeans or GMM based on silhouette score; DBSCAN is retained for academic comparison.
- Exposes model, cluster, playlist, saved playlist, and DJ chat behavior through FastAPI.
- Uses a React/Vite frontend for chat, cluster exploration, academic metrics, diagnostic plots, feature distributions, album cover preview, and saved playlists.

---

## Setup

### Prerequisites

- Python 3.10 or higher
- Node.js
- The approved Kaggle Spotify dataset CSV
- An [OpenRouter](https://openrouter.ai/) API key for the DJ agent
- Optional: a [Spotify Developer](https://developer.spotify.com/dashboard) app for enriching generated playlists with Spotify links and artwork

### 1. Install Python dependencies

```bash
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Create a `.env` file

Copy the example and fill in your keys:

```bash
copy .env.example .env
```

```text
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional, only needed for Spotify links and artwork enrichment
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
```

### 3. Add the approved Kaggle dataset

Download the approved Kaggle Spotify dataset and save the CSV as:

```text
data/raw/spotify_kaggle.csv
```

### 4. Collect and process data

```bash
.\.venv\Scripts\python.exe scripts\collect_data.py
```

Outputs:

- `data/raw/tracks_raw.csv` - normalized raw track data used by the pipeline
- `data/processed/tracks_features.csv` - cleaned audio features for every track
- `models/scaler.pkl` - fitted feature scaler

### 5. Train models and save artifacts

```bash
.\.venv\Scripts\python.exe scripts\train_pipeline.py
```

Outputs include PCA, selected clustering model, centroids, cluster metadata, t-SNE coordinates, and diagnostic plots under `models/`.

### 6. Run the backend

```bash
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --reload --port 8000
```

### 7. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend uses `VITE_API_BASE_URL=http://localhost:8000` by default.

---

## API Overview

- `GET /api/health` - model/artifact status.
- `GET /api/clusters` - cluster metadata and centroids.
- `GET /api/cluster-map` - real t-SNE points joined with track metadata.
- `GET /api/analysis` - model comparison, PCA report, k-search data, cluster metadata, diagnostic plot metadata, cohesion/separation rows, and generated report text.
- `GET /api/analysis/plots/{plot_name}` - whitelisted saved diagnostic plot images.
- `GET /api/feature-distributions` - boxplot-ready audio feature summaries by cluster.
- `POST /api/chat` - conversational DJ turn through OpenRouter.
- `POST /api/album-cover` - Pollinations album-cover URL generation.
- `GET/POST/DELETE /api/saved-playlists` - file-backed saved playlists under `data/saved_playlists`.

---

## Tests

Run backend tests with:

```bash
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Run frontend checks with:

```bash
cd frontend
npm run lint
npm run build
```

---

## Notes

- React/Vite is the only active user interface. The previous Streamlit app has been removed.
- Missing `OPENROUTER_API_KEY` returns a clear chat setup error, while non-chat model pages remain usable.
- Spotify credentials are optional. Without them, recommendations still work, but Spotify links and artwork enrichment may be skipped.
- The app does not use Spotify user authentication or playback; it is focused on exploration and recommendation.

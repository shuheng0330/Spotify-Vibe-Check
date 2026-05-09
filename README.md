# Spotify Vibe Check

Spotify Vibe Check is a Streamlit-based music exploration app that combines unsupervised audio-feature clustering with a conversational DJ agent.

The app groups tracks by acoustic profile, then lets users describe a mood or listening context in natural language. A Dynamic DJ agent interprets the request, selects the best cluster, and returns a playlist built from the cluster.

---

## What this project does

- Collects Spotify track metadata and audio features from seed playlists.
- Preprocesses audio features and scales them for clustering.
- Trains unsupervised models (PCA + KMeans/DBSCAN) to discover listening clusters.
- Builds a conversational interface that maps mood descriptions to clusters and playlist recommendations.
- Provides visual analysis of clusters, audio feature distributions, and model diagnostics.

---

## High-level flow

1. **Data collection** (`scripts/collect_data.py`): fetch track metadata and audio features from Spotify playlists listed in `data/playlists/seed_playlists.txt`.
2. **Preprocessing** (`src/data/preprocessor.py`): clean missing data, detect outliers, normalize audio features, and save the processed dataset.
3. **Training** (`scripts/train_pipeline.py`): perform PCA, run clustering algorithms, select the best model, build cluster metadata, and save diagnostic artifacts.
4. **App load** (`app/main.py`): load saved models and metadata through `src/utils/model_loader.py`.
5. **User interaction** (`app/pages/01_vibe_check.py`): user chat input is handled by `src/agent/dj_agent.py`, which uses Gemini to call defined tools and build playlists.
6. **Exploration pages**: visualize clusters (`app/pages/02_explore_clusters.py`) and review academic metrics (`app/pages/03_academic_analysis.py`).

---

## Project architecture

### Frontend

- `app/main.py` – main Streamlit entry point with sidebar navigation.
- `app/pages/01_vibe_check.py` – chat-based DJ interface.
- `app/pages/02_explore_clusters.py` – cluster visualization and profiles.
- `app/pages/03_academic_analysis.py` – silhouette, elbow curve, and evaluation report.
- `app/components/` – reusable plotting components:
  - `audio_radar.py` — radar charts for audio feature profiles.
  - `cluster_plot.py` — 2D cluster scatter and elbow plot.

### Backend

- `src/utils/model_loader.py` – loads saved machine learning models and supporting files.
- `src/data/spotify_collector.py` – Spotify data collection using the Spotify API.
- `src/data/preprocessor.py` – raw data cleaning, missing value handling, outlier detection, feature scaling.

### Machine learning

- `src/ml/dimensionality.py` – PCA and t-SNE transformation logic.
- `src/ml/clustering.py` – KMeans/DBSCAN training, evaluation, cluster naming, metadata generation.
- `src/ml/silhouette_analysis.py` – silhouette diagram, PCA scree plot, elbow curve, cohesion/separation metrics.

### Agent

- `src/agent/dj_agent.py` – Gemini-based conversational agent.
- `src/agent/tool_definitions.py` – function schemas exposed to Gemini.
- `src/agent/tool_handlers.py` – actual tool implementations that access the clustering models and dataset.

---

## Key files and responsibilities

- `requirements.txt` — Python dependency list.
- `scripts/collect_data.py` — data extraction from Spotify.
- `scripts/train_pipeline.py` — model training, evaluation, and artifact saving.
- `models/` — saved model files, centroids, metadata, plots, and diagnostic reports.
- `data/processed/tracks_features.csv` — processed dataset used by the app.
- `app/` — Streamlit app code and UI pages.
- `src/` — reusable Python modules for data, ML, and agent logic.

---

## Setup and run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a `.env` file

The project uses environment variables for API keys.

Required keys:

```text
GEMINI_API_KEY=your_google_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
```

### 3. Collect and process data

```bash
python scripts/collect_data.py
```

This generates:
- `data/processed/tracks_features.csv`
- `models/scaler.pkl`

### 4. Train models and save artifacts

```bash
python scripts/train_pipeline.py
```

This generates:
- `models/pca_model.pkl`
- `models/kmeans_model.pkl`
- `models/cluster_metadata.json`
- `models/tsne_2d.npy`
- diagnostic plots in `models/`

### 5. Run the Streamlit app

```bash
streamlit run app/main.py
```

---

## How the DJ agent works

The conversation agent is designed as a function-calling system:

1. It first assesses mood text and maps it to audio feature values.
2. It finds the closest acoustic cluster based on PCA-transformed centroids.
3. It generates a playlist from the selected cluster.
4. Optionally, it can compare clusters, refine the request, or generate album cover artwork.

The agent uses Gemini via `google-genai` and calls handler functions defined in `src/agent/tool_handlers.py`.

---

## Notes

- The app assumes `models/` and `data/processed/tracks_features.csv` are already generated.
- If the app cannot find saved models, it will display an error and ask you to run the data/train scripts first.
- The cluster naming is heuristic-based and derived from centroid audio feature patterns.
- The current version does not use Spotify playback or authentication for user accounts; it is focused on exploration and recommendation.

---

## Recommended order of work

1. Add Spotify playlist IDs to `data/playlists/seed_playlists.txt`.
2. Set up `.env` with API keys.
3. Run `python scripts/collect_data.py`.
4. Run `python scripts/train_pipeline.py`.
5. Launch the Streamlit app.

---

## Optional improvements

- Add a real Spotify playback integration.
- Improve the mood-to-feature mapping with a trained text model.
- Expand cluster naming and metadata generation.
- Cache more data for faster app startup.

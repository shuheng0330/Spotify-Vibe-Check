# Spotify Vibe Check

Spotify Vibe Check is a Streamlit-based music exploration app that combines unsupervised audio-feature clustering with a conversational DJ agent.

The app groups tracks by acoustic profile, then lets users describe a mood or listening context in natural language. A Dynamic DJ agent interprets the request, selects the best cluster, and returns a playlist built from that cluster.

---

## What this project does

- Collects Spotify track metadata and audio features from seed playlists via the Spotify API.
- Preprocesses and scales audio features, detects outliers.
- Reduces dimensionality with PCA, then competes KMeans against GMM — the better-scoring model wins.
- Builds a conversational interface that maps mood descriptions to clusters and playlist recommendations.
- Provides visual analysis of clusters, audio feature distributions, and model diagnostics.

---

## Setup

### Prerequisites

- Python 3.10 or higher
- A [Spotify Developer](https://developer.spotify.com/dashboard) app (Client ID + Secret)
- A [Google AI Studio](https://aistudio.google.com/app/apikey) API key for Gemini
- *(Optional)* An OpenAI API key for DALL-E album cover generation

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd spotify-vibe-check
pip install -r requirements.txt
```

### 2. Create a `.env` file

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

```text
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key_for_dalle_bonus   # optional
```

### 3. Add seed playlists

Open `data/playlists/seed_playlists.txt` and add one Spotify playlist ID per line. These are the playlists the collector will pull tracks from.

### 4. Collect and process data

```bash
python scripts/collect_data.py
```

Outputs:
- `data/processed/tracks_features.csv` — cleaned audio features for every track
- `models/scaler.pkl` — fitted feature scaler

### 5. Train models and save artifacts

```bash
python scripts/train_pipeline.py
```

Outputs:
- `models/pca_model.pkl` — fitted PCA transformer
- `models/kmeans_model.pkl` — the winning clustering model (KMeans or GMM)
- `models/cluster_centroids.pkl` — centroid coordinates in original feature space
- `models/cluster_metadata.json` — cluster names, sizes, representative tracks, and evaluation metrics
- `models/tsne_2d.npy` / `models/tsne_indices.npy` — 2D t-SNE embedding for visualization
- `models/silhouette_diagram.png`, `models/scree_plot.png`, `models/elbow_curve.png` — diagnostic plots
- `models/pca_report.json`, `models/k_eval.json` — numerical evaluation records

### 6. Run the app

```bash
streamlit run app/main.py
```

---

## How the training pipeline works

`scripts/train_pipeline.py` runs nine steps end-to-end:

| Step | What happens |
|------|-------------|
| 1 | **PCA** — reduces the scaled audio feature matrix to the minimum components that explain 95 % of variance. |
| 2 | **t-SNE** — fits a 2D embedding on a sample of up to 5,000 tracks for cluster visualization. |
| 3 | **k search** — tries KMeans for k = 3–14 on a subsample, ranks by silhouette score, picks the best k. |
| 4 | **KMeans** — fits KMeans with the best k on the full PCA-transformed dataset. |
| 5 | **GMM** — fits a Gaussian Mixture Model with the same number of components. |
| 6 | **Model selection** — compares KMeans vs GMM by silhouette score; the higher score wins. |
| 7 | **Cluster metadata** — names each cluster heuristically from centroid audio features, records representative tracks and top artists. |
| 8 | **Save** — serializes the winner model, centroids, and metadata to `models/`. |
| 9 | **Diagnostic plots** — writes silhouette diagram, PCA scree plot, and elbow curve. |

---

## KMeans vs GMM — why both?

KMeans assigns each track to exactly one cluster based on Euclidean distance to the nearest centroid. It works well when clusters are roughly spherical and similarly sized, but forces hard boundaries.

GMM (Gaussian Mixture Model) models each cluster as a multivariate Gaussian distribution. It learns the shape, orientation, and spread of each cluster, so it handles overlapping or elongated groups more naturally. Every track gets a probability of belonging to each cluster, and the highest probability wins.

Both models are trained with the same number of components (the best k found in Step 3). The one with the higher **silhouette score** — a measure of how well-separated and cohesive the clusters are — is kept as the production model. The evaluation results for both are stored in `cluster_metadata.json` and displayed on the Academic Analysis page.

---

## How the DJ agent works

The conversational agent is a function-calling system backed by Gemini:

1. It reads the user's mood text and maps it to Spotify audio feature values (energy, valence, danceability, etc.).
2. It finds the closest cluster by comparing the inferred feature vector against stored cluster centroids.
3. It builds a playlist by sampling tracks from the selected cluster.
4. Optionally it can compare clusters, refine the mood request, or generate an album cover image via DALL-E.

The agent calls handler functions defined in `src/agent/tool_handlers.py` through tool schemas in `src/agent/tool_definitions.py`.

---

## Project architecture

### Frontend (`app/`)

| File | Purpose |
|------|---------|
| `main.py` | Streamlit entry point with sidebar navigation |
| `pages/01_vibe_check.py` | Chat-based DJ interface |
| `pages/02_explore_clusters.py` | Cluster visualization and profiles |
| `pages/03_academic_analysis.py` | Silhouette, elbow curve, evaluation report |
| `components/audio_radar.py` | Radar charts for audio feature profiles |
| `components/cluster_plot.py` | 2D cluster scatter and elbow plot |

### Backend (`src/`)

| File | Purpose |
|------|---------|
| `data/spotify_collector.py` | Fetches track metadata and audio features via Spotipy |
| `data/preprocessor.py` | Cleans, imputes, detects outliers, scales features |
| `ml/dimensionality.py` | PCA and t-SNE logic |
| `ml/clustering.py` | KMeans and GMM training, evaluation, cluster naming |
| `ml/silhouette_analysis.py` | Diagnostic plot generation |
| `agent/dj_agent.py` | Gemini-based conversational agent |
| `agent/tool_definitions.py` | Function schemas exposed to Gemini |
| `agent/tool_handlers.py` | Tool implementations that query the clustering models |
| `utils/model_loader.py` | Loads saved model artifacts for the app |

---

## Notes

- The app expects `models/` and `data/processed/tracks_features.csv` to already exist. Run the collect and train scripts before launching.
- If saved models are missing the app will display an error with instructions.
- Cluster names are heuristic — derived from centroid audio feature values against hand-written rules in `src/ml/clustering.py`.
- The app does not use Spotify user authentication or playback; it is focused on exploration and recommendation.

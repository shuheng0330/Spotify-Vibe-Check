# Spotify Vibe Check — Project Report

**Module:** Unsupervised Machine Learning  
**Topic:** Conversational Audio-Feature Clustering  

---

## 1. Project Overview

Spotify Vibe Check is a full-stack machine learning application that maps songs into an acoustic latent space using unsupervised learning, then exposes that space through a conversational AI agent acting as a Dynamic DJ. Instead of relying on genre labels or collaborative filtering signals, the system clusters tracks purely by their numerical audio features — allowing mood-based, cold-start playlist generation from a single user message.

The application is architected as a **decoupled full-stack system**: a Python **FastAPI** backend serves the ML models and REST API, while a **React** (TypeScript + Vite) single-page application provides the interactive frontend. This separation allows the heavy ML inference to remain server-side while the UI stays responsive and independently deployable.

---

## 2. Dataset

### Why a Kaggle Dataset Instead of the Spotify Web API

The project requirement specifies the Spotify Web API as the data source. In practice, **direct large-scale collection via the API is no longer feasible** for two compounding reasons:

1. **Audio Features endpoint deprecated.** Spotify removed the `/audio-features` and `/audio-analysis` endpoints from the Web API in late 2024. These were the endpoints that returned the machine-learning-relevant fields (`energy`, `valence`, `danceability`, `acousticness`, `speechiness`, `instrumentalness`, `liveness`, `tempo`). Without them, the Spotify API only provides catalogue metadata (titles, artists, album art) — insufficient for any clustering task.

2. **Rate limits make bulk collection impractical.** Even before deprecation, collecting 200K+ tracks required navigating strict rate caps, OAuth token refresh loops, and playlist-seeding strategies that add days of wall-clock time to an academic project timeline.

**Resolution — Kaggle pre-extracted dataset.** The Kaggle corpus (`maharshipandya/spotify-tracks-dataset`, ~89K tracks; extended 300K variant also supported) was itself built from the Spotify API *before* the audio features deprecation. It contains the identical feature set the API once provided, making it a legitimate and reproducible stand-in.

| Aspect | Spotify Web API (2024) | Kaggle Dataset |
|--------|----------------------|----------------|
| Audio features available | ❌ Deprecated | ✅ Full feature set |
| Scale | Rate-limited | 89K – 300K tracks |
| Reproducibility | Variable (live data) | Fixed CSV snapshot |
| Setup complexity | OAuth + client credentials | Single CSV download |

> **Note:** The Spotify Web API is still used *after* clustering for playlist enrichment — the `sp.tracks()` endpoint (Client Credentials flow) remains active and is used to attach `spotify_url` and `artwork_url` to generated playlist tracks.

### Feature Set

Eight continuous audio features are used for all ML steps:

| Feature | Description | Range |
|---------|-------------|-------|
| `energy` | Perceptual intensity and activity | 0 – 1 |
| `valence` | Musical positiveness / mood | 0 – 1 |
| `danceability` | Rhythmic suitability for dancing | 0 – 1 |
| `acousticness` | Confidence that track is acoustic | 0 – 1 |
| `speechiness` | Presence of spoken words | 0 – 1 |
| `instrumentalness` | Predicts absence of vocals | 0 – 1 |
| `tempo` | Estimated beats per minute | ~50 – 220 |
| `mode` | Modality (major = 1, minor = 0) | 0 / 1 |

---

## 3. ML Pipeline

### 3.1 Preprocessing (`src/data/preprocessor.py`)

1. **Deduplication** — drop tracks sharing a `track_id`.
2. **Missing value imputation** — per-feature median fill; rows with more than 3 missing features are dropped.
3. **Outlier flagging** — IQR-based flag (`is_outlier`) retained as metadata; outliers are not removed to preserve musical edge cases.
4. **Feature scaling** — `StandardScaler` (zero mean, unit variance) applied to all 8 features. Scaled columns (`*_scaled`) are written alongside the originals so the agent can display human-readable values.

### 3.2 Dimensionality Reduction (`src/ml/dimensionality.py`)

**Principal Component Analysis (PCA)** is applied to the 8-dimensional scaled feature space.

- Components are selected automatically to explain **≥ 95% of total variance**.
- Minimum of 2 components is enforced to guarantee a valid distance metric.
- The resulting low-dimensional representation decorrelates features (e.g., `energy` and `loudness` are correlated) and reduces noise before clustering.
- **t-SNE** (2D) is computed separately on the PCA output for interactive visualisation only — it is not used for clustering or inference. Because t-SNE is computationally expensive at scale, it is applied to a random **subsample of 5 000 tracks** (`TSNE_SAMPLE_SIZE = 5000`) rather than the full dataset.

### 3.3 Clustering (`src/ml/clustering.py`)

Three algorithms are trained and evaluated competitively:

#### K-Means
- Optimal k searched over `k ∈ [3, 15]` using the **Elbow Method** (inertia) and **Silhouette Score** in tandem.
- Because `silhouette_score` has **O(n²)** time complexity, the k-search is performed on a random **subsample of 50 000 tracks** (`KSEARCH_SAMPLE_SIZE = 50000`) rather than the full dataset — making the search tractable even on 300K-track corpora.
- Final model uses `n_init=20` random restarts for stability.

#### Gaussian Mixture Model (GMM)
- Trained at the same optimal k as the winning K-Means run.
- Soft probabilistic cluster assignment; selected if its Silhouette Score exceeds K-Means.

#### DBSCAN
- ε estimated automatically from the 80th percentile of k-nearest-neighbour distances on a 10K-track subsample — avoids manual grid search.
- **Excluded from the winner selection** for a principled reason: scikit-learn's DBSCAN is transductive (no `predict()` for new points) and produces no centroid objects. The cold-start recommendation flow requires mapping an arbitrary mood vector to the nearest centroid at inference time; DBSCAN cannot support this. Its results are retained for academic comparison only.

#### Model Selection
```
winner = argmax(Silhouette Score)  over {K-Means, GMM}
```
Both the Silhouette Coefficient (higher = better, range −1 to +1) and Davies-Bouldin Index (lower = better) are reported. DBSCAN metrics are shown in the Academic Analysis page as a density-based baseline.

### 3.4 Cluster Naming (`src/ml/clustering.py`)

Each cluster centroid is matched against a rule table of 7 named vibe archetypes (e.g., *Party Anthems*, *Dark Drive*, *Acoustic Chill*, *Focus Flow*). A greedy unique-assignment algorithm ensures no two clusters share the same name: the highest-scoring (centroid, name) pair claims each name first. Unmatched clusters fall back to *Mixed Vibes*.

---

## 4. Conversational DJ Agent (`src/agent/`)

### 4.1 Architecture

The agent is implemented as a stateful multi-turn class (`DynamicDJAgent`) backed by **OpenRouter** (model: `z-ai/glm-4.5-air`) via the OpenAI-compatible SDK. Function calling (tool use) is the primary interaction pattern — the model never fabricates track names or feature values; it only responds with structured tool invocations that are executed server-side.

### 4.2 Tool Definitions

| Tool | Purpose |
|------|---------|
| `assess_mood` | Converts free-text mood description into a feature vector using a 30-keyword lookup table; returns a confidence score |
| `refine_preferences` | Triggered when confidence < 0.6; selects the most ambiguous feature and returns a targeted follow-up question |
| `find_cluster_for_mood` | Transforms the feature vector through the saved scaler → PCA pipeline, then finds the nearest cluster centroid by Euclidean distance in PCA space |
| `generate_playlist` | Samples tracks from the matched cluster; supports `random`, `popularity` sort modes and a `min_popularity` filter |
| `get_cluster_stats` | Returns centroid feature means, top artists, and representative tracks for any cluster |
| `compare_clusters` | Side-by-side feature delta between two clusters |
| `generate_album_cover` | Constructs a detailed image prompt from cluster statistics and requests artwork from the **Pollinations.ai** API (free, no authentication required) |

### 4.3 Cold-Start Resolution

The cold-start problem — recommending to a user with no listening history — is resolved by dialogue. The agent asks what mood or context the user is in, maps that description to a point in the trained acoustic space, and retrieves the closest cluster. No prior user data is required.

### 4.4 Spotify Enrichment

After playlist generation, each track ID is looked up via `spotipy.tracks()` (Spotify Client Credentials — still active as of 2025) to attach `spotify_url` and `artwork_url`. This step degrades gracefully: if credentials are absent or the API is unavailable, playlist generation continues without links.

On the frontend, every track row in the playlist table always renders a clickable Spotify button. If a direct `spotify_url` was returned by the enrichment step, the button opens that exact track on `open.spotify.com`. Otherwise it falls back to a Spotify search URL constructed from the track name and artist (`https://open.spotify.com/search/{track+artist}`), so users can always reach Spotify regardless of whether backend credentials are configured.

---

## 5. Application Architecture

The application uses a **decoupled client-server architecture** replacing the previous Streamlit prototype. This provides better performance, scalability, and a richer interactive experience.

### 5.1 Backend — FastAPI (`src/api/main.py`)

The backend is a **FastAPI** application that exposes a REST API consumed by the React frontend. It loads all ML model artefacts once at startup via `load_all()` (cached with `lru_cache`) and serves them across requests without re-loading from disk.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Model status, track count, cluster count, selected algorithm |
| `/api/clusters` | GET | All cluster metadata (name, centroid, top artists, representative tracks) |
| `/api/clusters/{id}/playlist` | GET | Sample tracks from a specific cluster |
| `/api/cluster-map` | GET | t-SNE 2D coordinates for the scatter visualisation |
| `/api/analysis` | GET | Full evaluation metrics, PCA report, k-search table, cohesion/separation, diagnostic plot availability |
| `/api/analysis/plots/{name}` | GET | Serves pre-generated diagnostic PNGs (elbow curve, silhouette diagram, etc.) |
| `/api/feature-distributions` | GET | Per-cluster feature boxplot data |
| `/api/chat` | POST | Forwards a user message to `DynamicDJAgent` and returns response + cluster + playlist |
| `/api/chat/reset` | POST | Resets the DJ agent conversation history |
| `/api/album-cover` | POST | Generates a Pollinations.ai image URL for a given cluster profile |
| `/api/saved-playlists` | GET / POST | List or persist a playlist to the local JSON store |
| `/api/saved-playlists/{id}` | DELETE | Remove a saved playlist |

CORS is configured to allow requests from any `localhost` or `127.0.0.1` origin, enabling the Vite dev server (`http://localhost:3000`) to call the FastAPI server (`http://localhost:8000`) during development.

### 5.2 Frontend — React + TypeScript (`frontend/`)

The frontend is a **React 18** single-page application built with **Vite** and styled with **Tailwind CSS v4**. All components are written in TypeScript.

| Page | Component | Content |
|------|-----------|---------|
| **Main** | `MainTab` | Project overview, 3-step how-to guide, feature grid, tech stack note |
| **Vibe Check** | `VibeCheckTab` | DJ chat panel + live playlist table (right); cluster cover image + 6-axis radar chart + feature sliders (left) |
| **Explore Clusters** | `ExploreClustersTab` | Interactive t-SNE scatter map with per-cluster colouring; feature distribution boxplots |
| **Academic Analysis** | `AcademicAnalysisTab` | Comparative performance matrix (KMeans / GMM / DBSCAN), PCA cumulative variance bar chart, K-search table, cohesion/separation table, diagnostic plot images, markdown analysis report |
| **Saved Playlists** | `SavedPlaylistsTab` / `PlaylistDetailTab` | Persisted playlist cards with track lists, audio profile and cover art |

The UI uses a dark glassmorphism design system: `#131313` background, `rgba(255,255,255,0.04)` glass panels, `#53E076` green accent, Inter / monospace fonts. Animations are handled by **Framer Motion**. Charts and the radar chart are rendered with custom SVG — no external charting library dependency for the core visualisations.

---

## 6. Deliverables

| Requirement | Implementation |
|-------------|---------------|
| Dimensionality reduction | PCA, 95% variance threshold, auto n_components |
| Clustering | K-Means + GMM (competitive), DBSCAN (academic baseline) |
| Cluster evaluation | Silhouette Coefficient, Davies-Bouldin Index, cohesion/separation ratio |
| Conversational agent | Multi-turn DynamicDJAgent, 7 tools, strict function-calling via OpenRouter |
| Cold-start playlist generation | Mood → feature vector → nearest centroid → sampled playlist |
| User-facing application | React + FastAPI full-stack, 5 pages, dark glassmorphism UI |
| Album cover generation *(bonus)* | Pollinations.ai via structured prompt derived from cluster centroid statistics |

---

## 7. Key Dependencies

### Backend (Python)
```
fastapi         — REST API framework
uvicorn         — ASGI server
scikit-learn    — PCA, t-SNE, K-Means, GMM, DBSCAN, Silhouette
pandas / numpy  — data wrangling and feature engineering
spotipy         — Spotify Web API (playlist enrichment only)
openai          — OpenRouter API client (function calling)
joblib          — model serialisation
python-dotenv   — environment variable management
```

### Frontend (Node.js / TypeScript)
```
react 18        — UI component framework
vite            — build tool and dev server
tailwindcss v4  — utility-first CSS (Vite plugin, no PostCSS config required)
typescript      — static typing
framer-motion   — page transition and micro-animations
lucide-react    — icon set
```

---

## 8. Reproducibility

1. Place the Kaggle CSV at `data/raw/spotify_kaggle.csv` (Schema A or B auto-detected).
2. Add API credentials to `.env`:
   ```
   OPENROUTER_API_KEY=...
   SPOTIPY_CLIENT_ID=...
   SPOTIPY_CLIENT_SECRET=...
   ```
3. Train the ML pipeline:
   ```bash
   python scripts/train_pipeline.py
   ```
   Outputs trained models and metadata to `models/`.

4. Start the FastAPI backend (default port 8000):
   ```bash
   uvicorn src.api.main:app --reload
   ```

5. Start the React frontend (default port 3000):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. Open `http://localhost:3000` — the Main page loads by default.

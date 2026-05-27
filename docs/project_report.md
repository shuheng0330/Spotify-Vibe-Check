# Spotify Vibe Check — Project Report

**Module:** Unsupervised Machine Learning  
**Topic:** Conversational Audio-Feature Clustering  

---

## 1. Project Overview

Spotify Vibe Check is a full-stack machine learning application that maps songs into an acoustic latent space using unsupervised learning, then exposes that space through a conversational AI agent acting as a Dynamic DJ. Instead of relying on genre labels or collaborative filtering signals, the system clusters tracks purely by their numerical audio features — allowing mood-based, cold-start playlist generation from a single user message.

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
- **t-SNE** (2D) is computed separately on the PCA output for interactive visualisation only — it is not used for clustering or inference.

### 3.3 Clustering (`src/ml/clustering.py`)

Three algorithms are trained and evaluated competitively:

#### K-Means
- Optimal k searched over `k ∈ [3, 15]` using the **Elbow Method** (inertia) and **Silhouette Score** in tandem.
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

---

## 5. Application (`app/`)

Built with **Streamlit** (wide layout, dark glassmorphism theme).

| Page | Content |
|------|---------|
| **Home** | Project intro, navigation, model status badge |
| **Vibe Check** | Two-column layout: cluster radar chart + album cover on the left; DJ chat + live playlist table on the right |
| **Explore Clusters** | Three tabs — t-SNE scatter map, per-cluster audio profiles (radar + top artists), feature distribution boxplots |
| **Academic Analysis** | Model comparison metrics, Silhouette diagram, PCA Scree plot, Elbow curve, cohesion/separation table, generated analysis report |
| **Saved Playlists** | Persisted playlist cards with track lists and audio profile expanders |

Plotly charts use `plotly_dark` with transparent backgrounds. Matplotlib uses `dark_background` context. All interactive charts display in the same colour palette (`#53E076` green accent, `#60A5FA` blue, `#F472B6` pink, `#FBBF24` amber).

---

## 6. Deliverables

| Requirement | Implementation |
|-------------|---------------|
| Dimensionality reduction | PCA, 95% variance threshold, auto n_components |
| Clustering | K-Means + GMM (competitive), DBSCAN (academic baseline) |
| Cluster evaluation | Silhouette Coefficient, Davies-Bouldin Index, cohesion/separation ratio |
| Conversational agent | Multi-turn DynamicDJAgent, 7 tools, strict function-calling |
| Cold-start playlist generation | Mood → feature vector → nearest centroid → sampled playlist |
| User-facing application | Streamlit, 5 pages, dark UI |
| Album cover generation *(bonus)* | Pollinations.ai via structured prompt derived from cluster centroid statistics |

---

## 7. Key Dependencies

```
scikit-learn    — PCA, t-SNE, K-Means, GMM, DBSCAN, Silhouette
pandas / numpy  — data wrangling and feature engineering
spotipy         — Spotify Web API (playlist enrichment only)
openai          — OpenRouter API client (function calling)
streamlit       — web application framework
plotly          — interactive charts
```

---

## 8. Reproducibility

1. Place the Kaggle CSV at `data/raw/spotify_kaggle.csv` (Schema A or B auto-detected).
2. Add API credentials to `.env` (`OPENROUTER_API_KEY`, `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`).
3. Run `python scripts/train_pipeline.py` — outputs trained models to `models/`.
4. Launch `streamlit run app/main.py`.

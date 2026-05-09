import numpy as np
import joblib
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


SCALED_FEATURE_COLS = [
    "energy_scaled", "valence_scaled", "danceability_scaled", "acousticness_scaled",
    "tempo_scaled", "loudness_scaled", "speechiness_scaled", "instrumentalness_scaled",
    "liveness_scaled", "mode_scaled",
]


def fit_pca(X: np.ndarray, variance_threshold: float = 0.95) -> tuple[PCA, np.ndarray, int]:
    pca_full = PCA(random_state=42)
    pca_full.fit(X)
    cumvar = np.cumsum(pca_full.explained_variance_ratio_)
    n_components = int(np.searchsorted(cumvar, variance_threshold)) + 1
    n_components = max(2, min(n_components, X.shape[1]))

    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X)
    print(f"PCA: {n_components} components explain {cumvar[n_components-1]:.1%} of variance")
    return pca, X_pca, n_components


def transform_pca(pca: PCA, X: np.ndarray) -> np.ndarray:
    return pca.transform(X)


def fit_tsne(X_pca: np.ndarray, perplexity: int = 40, random_state: int = 42) -> np.ndarray:
    perplexity = min(perplexity, X_pca.shape[0] // 4)
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=random_state, max_iter=1000)
    return tsne.fit_transform(X_pca)


def get_explained_variance_report(pca: PCA) -> dict:
    return {
        "individual": pca.explained_variance_ratio_.tolist(),
        "cumulative": np.cumsum(pca.explained_variance_ratio_).tolist(),
        "n_components": pca.n_components_,
    }


def save_pca(pca: PCA, path: str) -> None:
    joblib.dump(pca, path)


def load_pca(path: str) -> PCA:
    return joblib.load(path)

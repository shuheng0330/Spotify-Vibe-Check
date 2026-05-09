import numpy as np
import plotly.graph_objects as go
import plotly.express as px

PALETTE = px.colors.qualitative.Set2


def scatter_2d(
    X_2d: np.ndarray,
    labels: np.ndarray,
    track_names: list,
    artist_names: list,
    cluster_names: dict = None,
    title: str = "Cluster Map",
) -> go.Figure:
    unique_labels = sorted(set(labels))
    fig = go.Figure()
    for i, cid in enumerate(unique_labels):
        mask = labels == cid
        display_name = (cluster_names or {}).get(str(cid), f"Cluster {cid}") if cid != -1 else "Noise"
        fig.add_trace(go.Scatter(
            x=X_2d[mask, 0], y=X_2d[mask, 1],
            mode="markers",
            name=display_name,
            marker=dict(
                size=5,
                opacity=0.65,
                color=PALETTE[i % len(PALETTE)] if cid != -1 else "#cccccc",
            ),
            text=[f"<b>{t}</b><br>{a}" for t, a in
                  zip(np.array(track_names)[mask], np.array(artist_names)[mask])],
            hovertemplate="%{text}<extra></extra>",
        ))
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis_title="Dimension 1",
        yaxis_title="Dimension 2",
        legend_title="Cluster",
        height=500,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def elbow_plot(k_eval: dict) -> go.Figure:
    k_values = sorted(int(k) for k in k_eval.keys())
    inertias = [k_eval[str(k)]["inertia"] for k in k_values]
    silhouettes = [k_eval[str(k)]["silhouette"] for k in k_values]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=k_values, y=inertias, name="Inertia",
        mode="lines+markers", marker=dict(size=7),
        line=dict(color="steelblue"), yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=k_values, y=silhouettes, name="Silhouette",
        mode="lines+markers", marker=dict(size=7, symbol="square"),
        line=dict(color="darkorange", dash="dash"), yaxis="y2",
    ))
    fig.update_layout(
        title="Elbow Curve & Silhouette Scores",
        template="plotly_white",
        xaxis=dict(title="Number of Clusters (k)", tickmode="linear"),
        yaxis=dict(title="Inertia", side="left"),
        yaxis2=dict(title="Silhouette Score", side="right", overlaying="y"),
        legend=dict(x=0.7, y=0.95),
        height=380,
        margin=dict(l=50, r=50, t=50, b=40),
    )
    return fig

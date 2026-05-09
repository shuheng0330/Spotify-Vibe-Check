import plotly.graph_objects as go

RADAR_FEATURES = ["energy", "valence", "danceability", "acousticness",
                  "instrumentalness", "speechiness", "liveness"]


def radar_chart(feature_dict: dict, title: str = "") -> go.Figure:
    features = [f for f in RADAR_FEATURES if f in feature_dict]
    values = [feature_dict[f] for f in features]
    # Close the polygon
    features_closed = features + [features[0]]
    values_closed = values + [values[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=features_closed,
        fill="toself",
        fillcolor="rgba(29, 185, 84, 0.15)",
        line=dict(color="rgba(29, 185, 84, 0.8)", width=2),
        name=title,
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=11)),
        ),
        showlegend=False,
        template="plotly_white",
        title=dict(text=title, font=dict(size=13)),
        margin=dict(l=30, r=30, t=40, b=20),
        height=280,
    )
    return fig


def compare_radar(feature_dict_a: dict, feature_dict_b: dict, label_a: str, label_b: str) -> go.Figure:
    features = [f for f in RADAR_FEATURES if f in feature_dict_a and f in feature_dict_b]
    features_closed = features + [features[0]]

    fig = go.Figure()
    for feat_dict, label, color in [
        (feature_dict_a, label_a, "rgba(29, 185, 84, 0.6)"),
        (feature_dict_b, label_b, "rgba(30, 100, 200, 0.4)"),
    ]:
        values = [feat_dict[f] for f in features] + [feat_dict[features[0]]]
        fig.add_trace(go.Scatterpolar(
            r=values, theta=features_closed, fill="toself",
            name=label, line=dict(width=2),
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        template="plotly_white",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=30, r=30, t=30, b=40),
        height=300,
    )
    return fig

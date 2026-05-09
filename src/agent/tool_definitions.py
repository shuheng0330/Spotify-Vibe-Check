from google.genai import types

# ---------------------------------------------------------------------------
# Function declarations for all 7 Dynamic DJ tools.
# Used by dj_agent.py to configure the Gemini model.
# ---------------------------------------------------------------------------

_assess_mood = types.FunctionDeclaration(
    name="assess_mood",
    description=(
        "Parse the user's natural language mood or energy description and map it to "
        "estimated audio feature ranges. This MUST be the first tool called in every "
        "new conversation before any other tool."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "mood_description": types.Schema(
                type=types.Type.STRING,
                description="The user's raw text describing their mood, energy, or listening context.",
            ),
            "energy_level": types.Schema(
                type=types.Type.STRING,
                enum=["low", "medium", "high"],
                description="Optional explicit energy level if the user stated it clearly.",
            ),
            "valence_preference": types.Schema(
                type=types.Type.STRING,
                enum=["sad", "neutral", "happy"],
                description="Optional explicit emotional tone if the user stated it clearly.",
            ),
        },
        required=["mood_description"],
    ),
)

_find_cluster = types.FunctionDeclaration(
    name="find_cluster_for_mood",
    description=(
        "Given a feature vector produced by assess_mood, find the best matching cluster "
        "centroid using Euclidean distance in PCA space. Returns the cluster id, name, "
        "and a match score."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "energy": types.Schema(type=types.Type.NUMBER, description="Midpoint energy value (0-1)."),
            "valence": types.Schema(type=types.Type.NUMBER, description="Midpoint valence value (0-1)."),
            "danceability": types.Schema(type=types.Type.NUMBER, description="Midpoint danceability (0-1)."),
            "acousticness": types.Schema(type=types.Type.NUMBER, description="Midpoint acousticness (0-1)."),
            "instrumentalness": types.Schema(type=types.Type.NUMBER, description="Midpoint instrumentalness (0-1)."),
            "speechiness": types.Schema(type=types.Type.NUMBER, description="Midpoint speechiness (0-1)."),
            "liveness": types.Schema(type=types.Type.NUMBER, description="Midpoint liveness (0-1)."),
            "tempo": types.Schema(type=types.Type.NUMBER, description="Estimated BPM (e.g. 80-180)."),
            "loudness": types.Schema(type=types.Type.NUMBER, description="Estimated loudness in dB (e.g. -20 to 0)."),
            "mode": types.Schema(type=types.Type.NUMBER, description="0 for minor, 1 for major."),
            "top_n": types.Schema(type=types.Type.INTEGER, description="How many candidate clusters to return (1-3). Default 1."),
        },
        required=["energy", "valence", "danceability"],
    ),
)

_generate_playlist = types.FunctionDeclaration(
    name="generate_playlist",
    description=(
        "Build a curated playlist of N tracks from a specified cluster. "
        "Optionally filter by minimum popularity."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "cluster_id": types.Schema(type=types.Type.INTEGER, description="The cluster id to pull tracks from."),
            "n_tracks": types.Schema(type=types.Type.INTEGER, description="Number of tracks to return (default 10, max 30)."),
            "min_popularity": types.Schema(type=types.Type.INTEGER, description="Minimum Spotify popularity score 0-100 (default 0)."),
            "sort_by": types.Schema(
                type=types.Type.STRING,
                enum=["random", "popularity", "match_score"],
                description="How to order the returned tracks (default: random).",
            ),
        },
        required=["cluster_id"],
    ),
)

_get_cluster_stats = types.FunctionDeclaration(
    name="get_cluster_stats",
    description=(
        "Return a statistical summary of a cluster: mean audio features, track count, "
        "top artists, and a human-readable vibe description."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "cluster_id": types.Schema(type=types.Type.INTEGER, description="The cluster id to summarise."),
        },
        required=["cluster_id"],
    ),
)

_compare_clusters = types.FunctionDeclaration(
    name="compare_clusters",
    description=(
        "Compare two clusters side by side on all audio features. "
        "Use this when the user is undecided between two vibes."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "cluster_id_a": types.Schema(type=types.Type.INTEGER, description="First cluster id."),
            "cluster_id_b": types.Schema(type=types.Type.INTEGER, description="Second cluster id."),
        },
        required=["cluster_id_a", "cluster_id_b"],
    ),
)

_refine_preferences = types.FunctionDeclaration(
    name="refine_preferences",
    description=(
        "Generate a targeted follow-up question to narrow down cluster selection "
        "when the mood assessment confidence is below 0.6 or the user's description "
        "is ambiguous."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "ambiguous_features": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Audio feature names that are still uncertain.",
            ),
            "candidate_cluster_ids": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.INTEGER),
                description="Cluster ids that are currently plausible given what is known.",
            ),
        },
        required=["ambiguous_features", "candidate_cluster_ids"],
    ),
)

_generate_album_cover = types.FunctionDeclaration(
    name="generate_album_cover",
    description=(
        "Generate a DALL-E 3 album cover image based on the aggregate audio feature "
        "statistics of the current playlist. Only call this when the user explicitly "
        "asks for an album cover or artwork."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "cluster_name": types.Schema(type=types.Type.STRING, description="Name of the cluster/playlist."),
            "energy": types.Schema(type=types.Type.NUMBER, description="Mean energy of the playlist (0-1)."),
            "valence": types.Schema(type=types.Type.NUMBER, description="Mean valence of the playlist (0-1)."),
            "acousticness": types.Schema(type=types.Type.NUMBER, description="Mean acousticness (0-1)."),
            "instrumentalness": types.Schema(type=types.Type.NUMBER, description="Mean instrumentalness (0-1)."),
            "tempo": types.Schema(type=types.Type.NUMBER, description="Mean tempo (BPM)."),
            "style_hint": types.Schema(
                type=types.Type.STRING,
                description="Optional user-stated aesthetic preference (e.g. 'minimalist', 'vintage').",
            ),
        },
        required=["cluster_name", "energy", "valence"],
    ),
)

DJ_TOOL = types.Tool(
    function_declarations=[
        _assess_mood,
        _find_cluster,
        _generate_playlist,
        _get_cluster_stats,
        _compare_clusters,
        _refine_preferences,
        _generate_album_cover,
    ]
)

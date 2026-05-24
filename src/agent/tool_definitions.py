# Tool definitions for the Dynamic DJ agent in OpenAI function-calling format.
# Used by dj_agent.py when creating chat completions via OpenRouter.

DJ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "assess_mood",
            "description": (
                "Parse the user's natural language mood or energy description and map it to "
                "estimated audio feature ranges. This MUST be the first tool called in every "
                "new conversation before any other tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mood_description": {
                        "type": "string",
                        "description": "The user's raw text describing their mood, energy, or listening context.",
                    },
                    "energy_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Optional explicit energy level if the user stated it clearly.",
                    },
                    "valence_preference": {
                        "type": "string",
                        "enum": ["sad", "neutral", "happy"],
                        "description": "Optional explicit emotional tone if the user stated it clearly.",
                    },
                },
                "required": ["mood_description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_cluster_for_mood",
            "description": (
                "Given a feature vector produced by assess_mood, find the best matching cluster "
                "centroid using Euclidean distance in PCA space. Returns the cluster id, name, "
                "and a match score."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "energy":           {"type": "number", "description": "Midpoint energy value (0-1)."},
                    "valence":          {"type": "number", "description": "Midpoint valence value (0-1)."},
                    "danceability":     {"type": "number", "description": "Midpoint danceability (0-1)."},
                    "acousticness":     {"type": "number", "description": "Midpoint acousticness (0-1)."},
                    "instrumentalness": {"type": "number", "description": "Midpoint instrumentalness (0-1)."},
                    "speechiness":      {"type": "number", "description": "Midpoint speechiness (0-1)."},
                    "tempo":            {"type": "number", "description": "Estimated BPM (e.g. 80-180)."},
                    "mode":             {"type": "number", "description": "0 for minor, 1 for major."},
                    "top_n":            {"type": "integer", "description": "How many candidate clusters to return (1-3). Default 1."},
                },
                "required": ["energy", "valence", "danceability"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_playlist",
            "description": (
                "Build a curated playlist of N tracks from a specified cluster. "
                "Optionally filter by minimum popularity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_id":     {"type": "integer", "description": "The cluster id to pull tracks from."},
                    "n_tracks":       {"type": "integer", "description": "Number of tracks to return (default 10, max 30)."},
                    "min_popularity": {"type": "integer", "description": "Minimum Spotify popularity score 0-100 (default 0)."},
                    "sort_by": {
                        "type": "string",
                        "enum": ["random", "popularity", "match_score"],
                        "description": "How to order the returned tracks (default: random).",
                    },
                },
                "required": ["cluster_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cluster_stats",
            "description": (
                "Return a statistical summary of a cluster: mean audio features, track count, "
                "top artists, and a human-readable vibe description."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_id": {"type": "integer", "description": "The cluster id to summarise."},
                },
                "required": ["cluster_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_clusters",
            "description": (
                "Compare two clusters side by side on all audio features. "
                "Use this when the user is undecided between two vibes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_id_a": {"type": "integer", "description": "First cluster id."},
                    "cluster_id_b": {"type": "integer", "description": "Second cluster id."},
                },
                "required": ["cluster_id_a", "cluster_id_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "refine_preferences",
            "description": (
                "Generate a targeted follow-up question to narrow down cluster selection "
                "when the mood assessment confidence is below 0.6 or the user's description "
                "is ambiguous."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ambiguous_features": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Audio feature names that are still uncertain.",
                    },
                    "candidate_cluster_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Cluster ids that are currently plausible given what is known.",
                    },
                },
                "required": ["ambiguous_features", "candidate_cluster_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_album_cover",
            "description": (
                "Generate an AI album cover image using a free image generation API (no API key required). "
                "The image is built from the aggregate audio feature statistics of the current playlist. "
                "Always call this tool when the user asks for an album cover or artwork — it always works."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_name":     {"type": "string", "description": "Name of the cluster/playlist."},
                    "energy":           {"type": "number", "description": "Mean energy of the playlist (0-1)."},
                    "valence":          {"type": "number", "description": "Mean valence of the playlist (0-1)."},
                    "acousticness":     {"type": "number", "description": "Mean acousticness (0-1)."},
                    "instrumentalness": {"type": "number", "description": "Mean instrumentalness (0-1)."},
                    "tempo":            {"type": "number", "description": "Mean tempo (BPM)."},
                    "style_hint": {
                        "type": "string",
                        "description": "Optional user-stated aesthetic preference (e.g. 'minimalist', 'vintage').",
                    },
                },
                "required": ["cluster_name", "energy", "valence"],
            },
        },
    },
]

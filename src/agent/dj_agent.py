"""
Dynamic DJ agent — multi-turn conversational agent using Google Gemini
with strict function calling via the google-genai SDK.
"""
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.agent.tool_definitions import DJ_TOOL
from src.agent.tool_handlers import TOOL_DISPATCH

load_dotenv()

SYSTEM_PROMPT = """You are Dynamic DJ, a knowledgeable music curator assistant.
Your job is to understand the user's mood and musical preferences through conversation,
then use the available tools to find the right cluster of songs and build a playlist.

Rules you must follow:
1. Always call assess_mood as the FIRST tool in every new conversation.
2. Never invent track names, artist names, or feature values — only use data from tool results.
3. If assess_mood returns a confidence_score below 0.6, call refine_preferences before find_cluster_for_mood.
4. After finding a cluster, briefly explain what makes that cluster special before generating a playlist.
5. Only call generate_album_cover when the user explicitly requests artwork or an album cover.
6. Keep your tone helpful, concise, and conversational — like a knowledgeable friend who loves music.
7. Present playlists as a clean, readable list of track names and artists.
"""

MAX_TOOL_ITERATIONS = 6


class DynamicDJAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment. Check your .env file.")
        self.client = genai.Client(api_key=api_key)
        self._start_chat()

    def _start_chat(self):
        self.chat = self.client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                tools=[DJ_TOOL],
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )
        self._tool_calls_log: list[dict] = []
        self._current_cluster: dict | None = None
        self._current_playlist: list[dict] | None = None
        self._cover_url: str | None = None

    def send(self, user_message: str) -> tuple[str, list[dict]]:
        turn_log: list[dict] = []
        response = self.chat.send_message(user_message)

        for _ in range(MAX_TOOL_ITERATIONS):
            # Collect all function calls in this response
            fn_calls = [
                part.function_call
                for candidate in response.candidates
                for part in candidate.content.parts
                if part.function_call is not None
            ]
            if not fn_calls:
                break

            # Execute each function call and collect responses
            fn_responses = []
            for fc in fn_calls:
                fn_name = fc.name
                fn_args = dict(fc.args) if fc.args else {}
                try:
                    result = TOOL_DISPATCH[fn_name](**fn_args)
                except Exception as e:
                    result = {"error": str(e)}

                turn_log.append({"name": fn_name, "args": fn_args, "result": result})
                self._tool_calls_log.append({"name": fn_name})

                # Cache useful state for the UI
                if fn_name == "find_cluster_for_mood" and "cluster_id" in result:
                    self._current_cluster = result
                elif fn_name == "generate_playlist" and "playlist" in result:
                    self._current_playlist = result.get("playlist")
                elif fn_name == "generate_album_cover" and "image_url" in result:
                    self._cover_url = result.get("image_url")

                fn_responses.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result},
                    )
                )

            response = self.chat.send_message(fn_responses)

        # Extract final text
        text = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text

        return text.strip(), turn_log

    def reset(self):
        self._start_chat()

    @property
    def current_cluster(self) -> dict | None:
        return self._current_cluster

    @property
    def current_playlist(self) -> list[dict] | None:
        return self._current_playlist

    @property
    def cover_url(self) -> str | None:
        return self._cover_url

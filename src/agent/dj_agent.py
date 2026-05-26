"""
Dynamic DJ agent — multi-turn conversational agent using OpenRouter
with function calling via the openai SDK.
"""
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from src.agent.response_formatting import format_active_playlist_response
from src.agent.tool_definitions import DJ_TOOLS
from src.agent.tool_handlers import TOOL_DISPATCH

load_dotenv()

MODEL = "z-ai/glm-4.5-air:free"

SYSTEM_PROMPT = """You are Dynamic DJ, a knowledgeable music curator assistant.
Your job is to understand the user's mood and musical preferences through conversation,
then use the available tools to find the right cluster of songs and build a playlist.

Rules you must follow:
1. Call assess_mood as the FIRST tool in a new conversation, but NOT on every follow-up message.
2. Never invent track names, artist names, or feature values — only use data from tool results.
3. If assess_mood returns a confidence_score below 0.6, call refine_preferences to ask one clarifying question.
4. Once you have enough information, call find_cluster_for_mood AND then immediately call generate_playlist in the same turn before writing any text response.
5. After the playlist is generated, write a short friendly message explaining the cluster and listing a few highlight tracks.
6. Only call generate_album_cover when the user explicitly requests artwork or an album cover. This tool is FREE and always works — never refuse or apologize, just call it.
7. Keep your tone helpful, concise, and conversational — like a knowledgeable friend who loves music.
"""

MAX_TOOL_ITERATIONS = 10


class DynamicDJAgent:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment. Check your .env file.")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._start_chat()

    def _start_chat(self):
        self._messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._tool_calls_log: list[dict] = []
        self._current_cluster: dict | None = None
        self._current_playlist: list[dict] | None = None
        self._cover_url: str | None = None

    def send(self, user_message: str) -> tuple[str, list[dict]]:
        turn_log: list[dict] = []
        playlist_generated_this_turn = False
        self._messages.append({"role": "user", "content": user_message})

        final_text = ""
        for _ in range(MAX_TOOL_ITERATIONS):
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=self._messages,
                tools=DJ_TOOLS,
                temperature=0.7,
            )
            msg = response.choices[0].message

            # Append assistant turn to history
            assistant_entry: dict = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                assistant_entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ]
            self._messages.append(assistant_entry)

            if not msg.tool_calls:
                final_text = msg.content or ""
                break

            # Execute each tool call and append results
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments or "{}")
                try:
                    result = TOOL_DISPATCH[fn_name](**fn_args)
                except Exception as e:
                    result = {"error": str(e)}

                turn_log.append({"name": fn_name, "args": fn_args, "result": result})
                self._tool_calls_log.append({"name": fn_name})

                if fn_name == "find_cluster_for_mood" and "cluster_id" in result:
                    self._current_cluster = result
                elif fn_name == "generate_playlist" and "playlist" in result:
                    self._current_playlist = result.get("playlist")
                    playlist_generated_this_turn = True
                elif fn_name == "generate_album_cover" and "image_url" in result:
                    self._cover_url = result.get("image_url")

                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

        if not final_text.strip() and self._current_playlist:
            final_text = "Here's your playlist! Check it out below. Want me to generate an album cover for this vibe?"
        elif not final_text.strip():
            final_text = "Sorry, I had trouble processing that. Could you describe your mood again?"
        if playlist_generated_this_turn and self._current_playlist:
            final_text = format_active_playlist_response(
                cluster=self._current_cluster,
                playlist=self._current_playlist,
                assistant_text=final_text,
            )
        return final_text.strip(), turn_log

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

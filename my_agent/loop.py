"""The agent: the core think-act loop, now wrapped in a class so state lives
on the instance and so each stage of the loop *announces itself* on an event
bus. Notice there are no `print`s and no file writes in here anymore — the
loop's job is to run the conversation and publish what's happening. What to
*do* with those events (log, print to terminal, save a trajectory) is decided
by whoever subscribes, over in main.py. That decoupling is the whole point of
this refactor.
"""

import json

import requests

from my_agent.events import EventBus
from my_agent.tools import TOOLS, AVAILABLE_TOOLS

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."


class Agent:
    def __init__(
        self,
        bus: EventBus,
        model: str = "qwen3.6:35b-mlx",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        tools: list | None = None,
        available_tools: dict | None = None,
        ollama_url: str = OLLAMA_URL,
    ):
        self.bus = bus
        self.model = model
        self.tools = tools if tools is not None else TOOLS
        self.available_tools = (
            available_tools if available_tools is not None else AVAILABLE_TOOLS
        )
        self.ollama_url = ollama_url

        # Conversation state lives here and PERSISTS across run_turn() calls.
        # The system prompt is seeded exactly once, here — not per turn.
        self.messages: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]

    def call_llm(self) -> dict:
        """One round-trip to the model with the current conversation."""
        self.bus.emit("llm_start", messages=self.messages)
        response = requests.post(
            self.ollama_url,
            json={
                "model": self.model,
                "messages": self.messages,
                "tools": self.tools,
                "reasoning_effort": "none",
                "stream": False,
            },
        )
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]
        self.bus.emit("llm_end", message=message)
        return message

    def execute_tool(self, tool_call: dict) -> str:
        """Parse one tool call's arguments, dispatch to the function, run it.

        This is deliberately its own method: it's the natural seam where
        future permission checks and try/except error-recovery will live.
        """
        fn = tool_call["function"]
        name = fn["name"]
        args = json.loads(fn["arguments"])

        self.bus.emit("tool_start", name=name, args=args)
        func = self.available_tools[name]
        result = func(**args)
        self.bus.emit("tool_end", name=name, args=args, result=result)
        return str(result)

    def run_turn(self, user_input: str) -> None:
        """Handle one human turn: append the user message, then loop with the
        model (running any tools it requests) until it returns a plain answer.
        Mutates self.messages in place, so history accumulates across turns.
        """
        self.messages.append({"role": "user", "content": user_input})
        self.bus.emit("turn_start", user_input=user_input)

        while True:
            message = self.call_llm()
            self.messages.append(message)

            tool_calls = message.get("tool_calls")
            if not tool_calls:
                # No tools requested: this is the final answer for this turn.
                self.bus.emit("turn_end", message=message)
                return

            for tool_call in tool_calls:
                result = self.execute_tool(tool_call)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                })
            # Loop again so the model can see the tool results and respond.

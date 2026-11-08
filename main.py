"""Entry point. This file does three things and nothing else:
  1. create an event bus and subscribe handlers to it (all the side-effects:
     printing, logging, saving the trajectory),
  2. create the agent, wired to that bus,
  3. run the human input loop.

Notice the agent itself has no idea any of this is happening. It just emits
events. We decide here what those events *mean*. Want to silence tool-call
logging? Delete a subscribe line. Want to also stream events to a file or a
GUI later? Add a subscriber. The agent code never changes.
"""

import json

from my_agent import Agent, EventBus


# --- Subscribers: each is a plain function reacting to one event. ---

def log_tool_start(name, args):
    print(f"  [tool] {name}({args})")


def log_tool_end(name, args, result):
    print(f"  [tool] -> {result}")


def print_final_answer(message):
    content = message.get("content") or ""
    print(content)


def make_trajectory_saver(path, agent):
    """Returns a handler that dumps the full conversation after each turn.
    Closes over the agent so it can read agent.messages at save time.
    """
    def save(message):
        with open(path, "w") as f:
            json.dump(agent.messages, f, indent=2)
    return save


def main():
    bus = EventBus()
    agent = Agent(bus=bus)

    # Wire side-effects to events. Reorder/add/remove freely — the agent
    # neither knows nor cares which handlers exist.
    bus.subscribe("tool_start", log_tool_start)
    bus.subscribe("tool_end", log_tool_end)
    bus.subscribe("turn_end", print_final_answer)
    bus.subscribe("turn_end", make_trajectory_saver("./trajectory.json", agent))

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        agent.run_turn(user_input)


if __name__ == "__main__":
    main()

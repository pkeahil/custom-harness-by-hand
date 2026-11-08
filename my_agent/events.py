"""A minimal synchronous event bus (publish/subscribe).

This is intentionally tiny. The whole idea:
  - handlers register for a named event via `subscribe`
  - the agent announces things via `emit`
  - on emit, every handler registered for that event runs to completion,
    in registration order, before `emit` returns.

It is an *observer* bus: handlers react to events (log, print, save) but do
not modify the agent's data. That keeps the semantics simple and predictable.
If you later want handlers that *transform* data (redaction, context
compaction, vetoing a tool call), that's a different, more involved pattern
you can layer on top once you've felt the limits of this one.
"""

from collections import defaultdict
from typing import Callable


class EventBus:
    def __init__(self):
        # event name -> list of handler callables, in registration order.
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        """Register `handler` to be called whenever `event` is emitted."""
        self._handlers[event].append(handler)

    def emit(self, event: str, **payload) -> None:
        """Call every handler subscribed to `event`, in order.

        Handlers receive the payload as keyword arguments. This is a blocking,
        synchronous call: `emit` does not return until every handler has run.
        A handler that raises will propagate here; for a learning harness that
        is fine (it surfaces bugs loudly). You could wrap each call in
        try/except later if you want handlers to be isolated from each other.
        """
        for handler in self._handlers[event]:
            handler(**payload)

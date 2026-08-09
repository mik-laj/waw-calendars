"""Source fetchers. Each exposes ``fetch(client) -> list[Event]``."""

from . import expoxxi, waw4free, wola

FETCHERS = {
    "expoxxi": expoxxi.fetch,
    "waw4free": waw4free.fetch,
    "wola": wola.fetch,
}

__all__ = ["FETCHERS", "expoxxi", "waw4free", "wola"]

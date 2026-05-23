import asyncio
from typing import AsyncGenerator




class EventsManager:
    def __init__(self):
        self._subscribers: set[tuple[asyncio.AbstractEventLoop, asyncio.Queue[str]]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> AsyncGenerator[str, None]:
        loop = asyncio.get_running_loop()
        q: asyncio.Queue[str] = asyncio.Queue()
        async with self._lock:
            self._subscribers.add((loop, q))

        try:
            while True:
                event = await q.get()
                yield event
        finally:
            async with self._lock:
                self._subscribers.discard((loop, q))

    async def publish(self, event: str) -> None:
        async with self._lock:
            subs = list(self._subscribers)

        # on publie sans bloquer
        for _, q in subs:
            try:
                q.put_nowait(event)
            except Exception:
                # si un subscriber est en train de mourir, on ignore
                pass

    def publish_nowait(self, event: str) -> None:
        """Publie aussi depuis les routes synchrones FastAPI."""
        for loop, q in list(self._subscribers):
            try:
                loop.call_soon_threadsafe(q.put_nowait, event)
            except Exception:
                pass


events_manager = EventsManager()


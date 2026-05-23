import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.events_manager import events_manager


router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/erp", response_class=StreamingResponse)
async def erp_events(request: Request) -> StreamingResponse:
    """SSE: envoie des events liés à l'ERP (ex: dossiers modifiés)."""

    async def event_stream() -> AsyncGenerator[bytes, None]:
        # ping initial pour que le client sache que ça marche
        yield b"event: ping\ndata: {}\n\n"

        async for event in events_manager.subscribe():
            if await request.is_disconnected():
                break
            # event contient une chaîne JSON déjà sérialisée
            yield f"event: erp\ndata: {event}\n\n".encode("utf-8")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def make_event(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


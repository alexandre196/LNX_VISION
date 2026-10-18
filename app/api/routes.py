from fastapi import APIRouter, Query
from fastapi.responses import Response
from app.core.analysis import (
    shortest_path, get_all_entities, get_entity,
    get_entity_events, get_high_risk, get_graph_stats, get_communities,
)
from app.core.report import generate_entity_report, generate_global_report

router = APIRouter()


@router.get("/shortest-path")
async def route_shortest_path(start: str = Query(...), end: str = Query(...)):
    return shortest_path(start, end)


@router.get("/entities")
async def route_get_entities():
    return {"entities": get_all_entities(), "total": len(get_all_entities())}


@router.get("/entities/{entity_id}")
async def route_get_entity(entity_id: str):
    return get_entity(entity_id)


@router.get("/entities/{entity_id}/events")
async def route_get_events(entity_id: str):
    """Événements / timeline d'une entité."""
    events = get_entity_events(entity_id)
    return {"entity_id": entity_id, "count": len(events), "events": events}


@router.get("/alerts")
async def route_alerts(threshold: int = Query(75)):
    results = get_high_risk(threshold)
    return {"threshold": threshold, "count": len(results), "entities": results}


@router.get("/communities")
async def route_communities():
    """Détection automatique de communautés — algorithme de Louvain."""
    return get_communities()


@router.get("/stats")
async def route_stats():
    return get_graph_stats()


@router.get("/report/global")
async def route_report_global():
    pdf_bytes = generate_global_report()
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=nexus_rapport_global.pdf"})


@router.get("/report/{entity_id}")
async def route_report_entity(entity_id: str):
    pdf_bytes = generate_entity_report(entity_id)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=nexus_{entity_id}.pdf"})
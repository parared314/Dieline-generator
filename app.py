#!/usr/bin/env python3
import io
import json
from dataclasses import asdict

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from dieline.registry import TemplateRegistry

app = FastAPI(title="Dieline Generator")
registry = TemplateRegistry()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()


@app.get("/api/templates")
async def list_templates():
    """List all available packaging templates."""
    return [t.metadata() for t in registry.all()]


@app.get("/api/templates/{template_id}/schema")
async def get_schema(template_id: str):
    """Return parameter specs for a template so the frontend can build a form."""
    tmpl = registry.get(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    specs = tmpl.parameter_specs()
    return {
        "template_id": template_id,
        "parameters": [asdict(s) for s in specs],
        "defaults": tmpl.default_params(),
    }


@app.post("/api/render")
async def render_preview(body: dict):
    """
    Generate an SVG for live preview.
    Request: {"template_id": "tuck_top_box", "params": {"width": 80, ...}}
    Response: SVG string (image/svg+xml)
    """
    template_id = body.get("template_id", "")
    tmpl = registry.get(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    params = body.get("params", {})
    svg, errors = tmpl.render(params)
    if errors:
        raise HTTPException(status_code=422, detail=[asdict(e) for e in errors])

    return HTMLResponse(content=svg, media_type="image/svg+xml")


@app.get("/api/download/{template_id}")
async def download_svg(template_id: str, params: str = Query(...)):
    """
    Download a fully generated SVG file.
    params is a JSON-encoded string of the dimension values.
    """
    tmpl = registry.get(template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        param_dict = json.loads(params)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid params JSON")

    svg, errors = tmpl.render(param_dict)
    if errors:
        raise HTTPException(status_code=422, detail=[asdict(e) for e in errors])

    buf = io.BytesIO(svg.encode("utf-8"))
    filename = f"{template_id}_dieline.svg"
    return StreamingResponse(
        buf,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

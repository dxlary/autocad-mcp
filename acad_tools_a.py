"""AutoCAD MCP tools, batch A (inspection + basic drawing)."""
from __future__ import annotations

import acad_com
from acad_com import (
    CadError,
    _com_call,
    _flat,
    _geom,
    _need_doc,
    _pt,
    get_app,
)
from acad_core import tool


@tool("autocad_status", """
    Report whether AutoCAD is reachable: version, active drawing, entity count.
    Safe to call at any time - never launches AutoCAD.
""")
def autocad_status(progid: str = "") -> dict:
    try:
        app = get_app(launch=False)
    except CadError as e:
        return {"connected": False, "message": str(e)}
    info = {
        "connected": True,
        "progid": acad_com._app_progid,
        "version": _com_call(lambda: str(app.Version)),
        "caption": _com_call(lambda: str(app.Caption)),
        "document_count": _com_call(lambda: int(app.Documents.Count)),
    }
    try:
        doc = app.ActiveDocument
        info["drawing"] = str(doc.Name)
        info["path"] = str(doc.Path)
        info["model_space_entities"] = int(doc.ModelSpace.Count)
        info["layers"] = int(doc.Layers.Count)
    except Exception as e:  # noqa: BLE001
        info["drawing"] = None
        info["note"] = f"no active drawing ({e})"
    return info


@tool("autocad_connect", """
    Attach to a running AutoCAD, or start one when launch=true.
    launch=true starts AutoCAD (30-60s); leave it false for the normal case
    where AutoCAD is already open.
""")
def autocad_connect(launch: bool = False, progid: str = "") -> dict:
    app = get_app(launch=launch, progid=progid)
    return {
        "connected": True,
        "progid": acad_com._app_progid,
        "version": _com_call(lambda: str(app.Version)),
        "document_count": _com_call(lambda: int(app.Documents.Count)),
    }


@tool("autocad_list_layers",
      "List every layer in the active drawing with colour, linetype and state.")
def autocad_list_layers(progid: str = "") -> dict:
    doc = _need_doc()
    layers = []
    for i in range(doc.Layers.Count):
        try:
            la = doc.Layers.Item(i)
            layers.append({
                "name": str(la.Name),
                "color": int(la.Color),
                "linetype": str(la.Linetype),
                "on": bool(la.LayerOn),
                "frozen": bool(la.Freeze),
                "locked": bool(la.Lock),
            })
        except Exception as e:  # noqa: BLE001
            layers.append({"name": f"<layer {i}>", "error": str(e)})
    return {"count": len(layers), "layers": layers}


@tool("autocad_list_entities", """
    Enumerate model-space entities, optionally filtered by layer and/or type.
    entity_type is a case-insensitive substring: Line, Polyline, Circle,
    Text, Solid, Hatch, ...
""")
def autocad_list_entities(
    layer: str = "", entity_type: str = "", limit: int = 200, progid: str = ""
) -> dict:
    doc = _need_doc()
    ms = doc.ModelSpace
    total = int(ms.Count)
    out = []
    for i in range(total):
        if len(out) >= limit:
            break
        try:
            e = ms.Item(i)
            etype = str(e.EntityName)
            elayer = str(e.Layer)
            if layer and elayer.lower() != layer.lower():
                continue
            if entity_type and entity_type.lower() not in etype.lower():
                continue
            row = {"index": i, "type": etype, "layer": elayer,
                   "handle": str(e.Handle)}
            row.update(_geom(e))
            out.append(row)
        except Exception as e:  # noqa: BLE001
            out.append({"index": i, "error": str(e)})
    return {
        "total_in_model_space": total,
        "returned": len(out),
        "truncated": len(out) >= limit,
        "entities": out,
    }


@tool("autocad_get_extents",
      "Return the drawing bounding box (EXTMIN / EXTMAX).")
def autocad_get_extents(progid: str = "") -> dict:
    doc = _need_doc()
    return {
        "extmin": [round(float(c), 4) for c in doc.GetVariable("EXTMIN")],
        "extmax": [round(float(c), 4) for c in doc.GetVariable("EXTMAX")],
    }


@tool("autocad_draw_line", "Draw a line from (x1,y1) to (x2,y2) in model space.")
def autocad_draw_line(
    x1: float, y1: float, x2: float, y2: float,
    z1: float = 0.0, z2: float = 0.0, layer: str = "", progid: str = "",
) -> dict:
    doc = _need_doc()
    ent = _com_call(doc.ModelSpace.AddLine, _pt(x1, y1, z1), _pt(x2, y2, z2))
    if layer:
        ent.Layer = layer
    return {"ok": True, "handle": str(ent.Handle), "type": str(ent.EntityName)}


@tool("autocad_draw_polyline", """
    Draw a 2D lightweight polyline.
    points is a flat list: [x1,y1,x2,y2,...]
""")
def autocad_draw_polyline(
    points: list, closed: bool = False, layer: str = "", progid: str = ""
) -> dict:
    if len(points) < 4 or len(points) % 2 != 0:
        raise CadError("points must be a flat even-length list: [x1,y1,x2,y2,...]")
    doc = _need_doc()
    ent = _com_call(doc.ModelSpace.AddLightWeightPolyline, _flat(points))
    if closed:
        ent.Closed = True
    if layer:
        ent.Layer = layer
    return {"ok": True, "handle": str(ent.Handle),
            "vertices": len(points) // 2, "closed": closed}


@tool("autocad_draw_circle",
      "Draw a circle with centre (cx,cy) and the given radius.")
def autocad_draw_circle(
    cx: float, cy: float, radius: float, layer: str = "", progid: str = ""
) -> dict:
    if radius <= 0:
        raise CadError("radius must be > 0")
    doc = _need_doc()
    ent = _com_call(doc.ModelSpace.AddCircle, _pt(cx, cy), float(radius))
    if layer:
        ent.Layer = layer
    return {"ok": True, "handle": str(ent.Handle), "radius": float(radius)}


@tool("autocad_draw_text",
      "Place single-line text at (x,y). rotation is in degrees.")
def autocad_draw_text(
    text: str, x: float, y: float, height: float = 2.5,
    rotation: float = 0.0, layer: str = "", progid: str = "",
) -> dict:
    doc = _need_doc()
    ent = _com_call(doc.ModelSpace.AddText, str(text), _pt(x, y), float(height))
    try:
        ent.Rotation = float(rotation) * 3.141592653589793 / 180.0
    except Exception:  # noqa: BLE001
        pass
    if layer:
        ent.Layer = layer
    return {"ok": True, "handle": str(ent.Handle), "text": str(text)}

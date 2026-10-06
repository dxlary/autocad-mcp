"""AutoCAD MCP tools, batch B (layers, variables, commands, files)."""
from __future__ import annotations

import acad_com
from acad_com import (
    CadError,
    _com_call,
    _need_doc,
    get_app,
)
from acad_core import tool


@tool("autocad_ensure_layer", """
    Create a layer if missing, set its colour, optionally make it current.
    color is an ACI index: 1 red, 2 yellow, 3 green, 4 cyan, 5 blue,
    6 magenta, 7 white/black.
""")
def autocad_ensure_layer(
    name: str, color: int = 7, make_current: bool = True, progid: str = ""
) -> dict:
    doc = _need_doc()
    try:
        la = doc.Layers.Add(name)
        created = True
    except Exception:  # noqa: BLE001
        la = doc.Layers.Item(name)
        created = False
    try:
        la.Color = int(color)
    except Exception:  # noqa: BLE001
        pass
    if make_current:
        doc.ActiveLayer = la
    return {"ok": True, "layer": str(name), "created": created,
            "color": int(color)}


@tool("autocad_get_variable",
      "Read an AutoCAD system variable (FILLMODE, OSMODE, LUNITS, ...).")
def autocad_get_variable(name: str, progid: str = "") -> dict:
    doc = _need_doc()
    return {"name": str(name), "value": _com_call(doc.GetVariable, name)}


@tool("autocad_set_variable",
      "Set an AutoCAD system variable. Pass value as a number or string.")
def autocad_set_variable(name: str, value: str = "", progid: str = "") -> dict:
    doc = _need_doc()
    _com_call(doc.SetVariable, name, value)
    return {"ok": True, "name": str(name), "value": value}


@tool("autocad_run_command", """
    Send a command-line string to AutoCAD; accepts AutoLISP expressions.
    Use AutoCAD syntax with trailing spaces, e.g. "_ZOOM _E " or
    (command "_LINE" "0,0" "10,10" "") . Execution is asynchronous, so poll
    autocad_status or autocad_get_extents afterwards to confirm the result.
""")
def autocad_run_command(command: str, progid: str = "") -> dict:
    doc = _need_doc()
    _com_call(doc.SendCommand, str(command))
    return {"ok": True, "sent": str(command), "async": True}


@tool("autocad_zoom_extents", "Zoom to the drawing extents.")
def autocad_zoom_extents(progid: str = "") -> dict:
    app = get_app()
    _com_call(app.ZoomExtents)
    return {"ok": True}


@tool("autocad_save",
      "Save the active drawing. With path, save a copy to that location.")
def autocad_save(path: str = "", progid: str = "") -> dict:
    doc = _need_doc()
    if path:
        _com_call(doc.SaveAs, path)
        return {"ok": True, "saved_as": path}
    _com_call(doc.Save)
    return {"ok": True, "saved": str(doc.Name)}


@tool("autocad_new_drawing",
      "Create a new drawing, optionally from a .dwt template.")
def autocad_new_drawing(template: str = "", progid: str = "") -> dict:
    app = get_app()
    doc = _com_call(app.Documents.Add, template) if template else _com_call(
        app.Documents.Add
    )
    return {"ok": True, "name": str(doc.Name)}


@tool("autocad_open_drawing", "Open an existing DWG/DXF by absolute path.")
def autocad_open_drawing(path: str, progid: str = "") -> dict:
    app = get_app()
    doc = _com_call(app.Documents.Open, path)
    return {"ok": True, "name": str(doc.Name), "path": str(doc.Path)}

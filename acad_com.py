"""Windows COM / ActiveX bridge to AutoCAD (pywin32, late binding)."""
from __future__ import annotations

import logging
import os
import sys

import pythoncom  # noqa: E402
import pywintypes  # noqa: E402
import win32com.client  # noqa: E402

log = logging.getLogger("autocad-mcp")

# Version-independent ProgID resolves to the newest registered AutoCAD, so it
# is tried first; explicit versions are fallbacks. Override with AUTOCAD_PROGID.
#   .25.1=2026 .25=2025 .24.3=2024 .24.2=2023 .24.1=2022 .24=2021
#   .23.1=2020 .23=2019 .22=2018
PROGID_CHAIN = [
    "AutoCAD.Application",
    "AutoCAD.Application.25.1",
    "AutoCAD.Application.25",
    "AutoCAD.Application.24.3",
    "AutoCAD.Application.24.2",
    "AutoCAD.Application.24.1",
    "AutoCAD.Application.24",
    "AutoCAD.Application.23.1",
    "AutoCAD.Application.23",
    "AutoCAD.Application.22",
]

if os.environ.get("AUTOCAD_PROGID", "").strip():
    PROGID_CHAIN = [os.environ["AUTOCAD_PROGID"].strip()] + PROGID_CHAIN

_app = None
_app_progid = None


class CadError(RuntimeError):
    """An error the caller can act on (not a crash)."""


def _pt(x, y, z=0.0):
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), float(z)]
    )


def _flat(vals):
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in vals]
    )


def _com_call(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except pywintypes.com_error as e:
        raise CadError(f"COM call failed: {e}") from e
    except AttributeError as e:
        raise CadError(
            f"AutoCAD object does not expose this member ({e}); "
            "the document may be read-only or a different object type."
        ) from e


def get_app(launch: bool = False, progid: str = ""):
    global _app, _app_progid
    if _app is not None:
        try:
            _ = _app.Documents.Count
            return _app
        except Exception:  # noqa: BLE001
            log.warning("cached AutoCAD handle is dead, reconnecting")
            _app = None
            _app_progid = None

    pythoncom.CoInitialize()
    candidates = [progid] if progid else PROGID_CHAIN
    for pid in candidates:
        try:
            app = win32com.client.GetActiveObject(pid)
            _app, _app_progid = app, pid
            log.info("attached to running AutoCAD via %s", pid)
            return app
        except Exception as e:  # noqa: BLE001
            log.debug("GetActiveObject(%s) -> %s", pid, e)
            continue

    if launch:
        pid = progid or PROGID_CHAIN[0]
        try:
            app = win32com.client.Dispatch(pid)
            app.Visible = True
            _app, _app_progid = app, pid
            log.info("launched AutoCAD via %s", pid)
            return app
        except pywintypes.com_error as e:
            raise CadError(f"could not launch {pid}: {e}") from e

    raise CadError(
        "AutoCAD is not running. Start AutoCAD and open a DWG first, "
        "or call autocad_connect with launch=true."
    )


def get_doc(launch: bool = False, progid: str = ""):
    app = get_app(launch=launch, progid=progid)
    try:
        if app.Documents.Count == 0:
            return None
        return app.ActiveDocument
    except Exception as e:  # noqa: BLE001
        raise CadError(f"could not read active document: {e}") from e


def _need_doc(launch: bool = False, progid: str = ""):
    doc = get_doc(launch=launch, progid=progid)
    if doc is None:
        raise CadError(
            "AutoCAD is running but no drawing is open. Open a DWG, "
            "or call autocad_new_drawing."
        )
    return doc


def _geom(entity) -> dict:
    out = {}
    for attr in (
        "StartPoint", "EndPoint", "Center", "Radius", "InsertionPoint",
        "Height", "TextString", "Coordinates", "Length", "Area",
    ):
        try:
            v = getattr(entity, attr)
            if isinstance(v, tuple):
                v = [round(float(c), 4) for c in v]
            elif isinstance(v, float):
                v = round(v, 4)
            out[attr] = v
        except Exception:  # noqa: BLE001
            pass
    return out

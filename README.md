# autocad-mcp

Let WorkBuddy (or any MCP client) drive AutoCAD through COM automation.

https://github.com/dxlary/autocad-mcp

Zero third-party dependencies except `pywin32` — the MCP protocol layer is
implemented with the standard library, so this installs offline and never
breaks because PyPI is down.

## What you need

| Requirement | Note |
|---|---|
| Windows | COM/ActiveX is Windows-only |
| Full AutoCAD, **not LT** | AutoCAD LT exposes no automation interface |
| AutoCAD 2018 – 2026 | Located automatically by ProgID |
| Python 3.10+ | Any interpreter with `pywin32` |

AutoCAD must be running with a drawing open. Tools return a clear message when
it is not, rather than crashing.

## Install

```bat
pip install pywin32
```

Or install straight from GitHub, which also gives you an `autocad-mcp`
command so the config below becomes just `"command": "autocad-mcp"`:

```bat
pip install git+https://github.com/dxlary/autocad-mcp.git
```

## Register with WorkBuddy

Add this to `%USERPROFILE%\.workbuddy\mcp.json`, replacing the two paths with
your own Python interpreter and the location you saved `server.py` to:

```json
{
  "mcpServers": {
    "autocad-mcp": {
      "command": "C:\\Path\\To\\python.exe",
      "args": ["C:\\Path\\To\\autocad-mcp\\server.py"]
    }
  }
}
```

Then open WorkBuddy's connector management page, find `autocad-mcp` under
custom connectors, and click **Trust**. Manually added MCP servers do not
activate on their own.

## Verify without AutoCAD

```bat
python server.py --selftest   % 12 checks, no AutoCAD needed
python server.py --probe      % print the tools/list payload
```

## Tools (17)

| Tool | Purpose |
|---|---|
| `autocad_status` | Version, active drawing, entity count |
| `autocad_connect` | Attach, or start AutoCAD with `launch=true` |
| `autocad_list_layers` | All layers with colour, linetype, state |
| `autocad_list_entities` | Model-space entities, filter by layer/type |
| `autocad_get_extents` | EXTMIN / EXTMAX bounding box |
| `autocad_draw_line` | Line between two points |
| `autocad_draw_polyline` | 2D polyline from a flat coordinate list |
| `autocad_draw_circle` | Circle by centre and radius |
| `autocad_draw_text` | Single-line text |
| `autocad_ensure_layer` | Create layer, set ACI colour, make current |
| `autocad_get_variable` | Read a system variable |
| `autocad_set_variable` | Write a system variable |
| `autocad_run_command` | Send a command string or AutoLISP |
| `autocad_zoom_extents` | Zoom to extents |
| `autocad_save` | Save, or save-as to a path |
| `autocad_new_drawing` | New drawing, optionally from a .dwt |
| `autocad_open_drawing` | Open a DWG/DXF by path |

## Notes

- **Colour is ACI only** (1 red, 2 yellow, 3 green, 4 cyan, 5 blue,
  6 magenta, 7 white/black). The ActiveX `Color` property has no true-colour
  channel.
- **Solid fill**: `AddHatch` does not fill unless you append loops, and 3D
  faces never fill. For solid shapes use 2D SOLID entities, or import an
  R12 (`AC1009`) DXF via `autocad_run_command` with `._INSERT`/`-IMPORT`.
- **`autocad_run_command` is asynchronous.** Poll `autocad_status` or
  `autocad_get_extents` afterwards to confirm the result.
- **Pin a version** by setting `AUTOCAD_PROGID`, e.g.
  `AUTOCAD_PROGID=AutoCAD.Application.24.1` for 2022.
- **AutoCAD itself is commercial software.** This project is not affiliated
  with Autodesk; you are responsible for your own AutoCAD licence.

## License

MIT. See [LICENSE](LICENSE).

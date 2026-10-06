"""
autocad-mcp - WorkBuddy <-> AutoCAD COM bridge (stdio MCP server)

This file is the entry point: it wires up the tool registry (defined across
acad_com / acad_tools_a / acad_tools_b) and implements the stdio MCP
transport with the standard library only. Zero third-party dependencies
beyond pywin32.

Run:   python server.py            (stdio transport, launched by WorkBuddy)
Test:  python server.py --selftest (no AutoCAD required)
Probe: python server.py --probe    (prints the tools/list payload)
"""

from __future__ import annotations

import inspect
import json
import logging
import sys

import acad_core
import acad_tools_a  # noqa: F401  (registers its tools on import)
import acad_tools_b  # noqa: F401  (registers its tools on import)

# stdout is the MCP transport: all diagnostics must go to stderr.
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[autocad-mcp] %(levelname)s %(message)s",
)

TOOLS = acad_core.TOOLS


def _tools_payload() -> list:
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "inputSchema": t["inputSchema"],
        }
        for t in TOOLS.values()
    ]


def _result_text(value) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    except Exception:  # noqa: BLE001
        return str(value)


def _call_tool(name: str, arguments: dict) -> dict:
    entry = TOOLS.get(name)
    if entry is None:
        return {"content": [{"type": "text", "text": f"unknown tool: {name}"}],
                "isError": True}
    try:
        args = arguments or {}
        allowed = inspect.signature(entry["fn"]).parameters
        args = {k: v for k, v in args.items() if k in allowed}
        value = entry["fn"](**args)
        return {"content": [{"type": "text", "text": _result_text(value)}],
                "isError": False}
    except acad_core.CadError as e:
        return {"content": [{"type": "text", "text": str(e)}], "isError": True}
    except Exception as e:  # noqa: BLE001
        logging.exception("tool %s raised", name)
        return {"content": [{"type": "text",
                             "text": f"{type(e).__name__}: {e}"}],
                "isError": True}


def handle(msg: dict):
    """Dispatch one JSON-RPC message. Returns a response dict or None."""
    method = msg.get("method")
    mid = msg.get("id")

    def ok(result):
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def err(code, message):
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": code, "message": message}}

    if method is None:
        return None
    if method.startswith("notifications/"):
        return None

    if method == "initialize":
        return ok({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "autocad-mcp", "version": "0.1.0"},
        })
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": _tools_payload()})
    if method == "tools/call":
        params = msg.get("params") or {}
        return ok(_call_tool(params.get("name", ""), params.get("arguments")))

    return err(-32601, f"method not found: {method}")


def serve() -> None:
    logging.info("autocad-mcp starting on stdio")
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        # Tolerate Content-Length style framing: header lines are not JSON.
        if line.startswith("Content-Length") or line.startswith("Content-Type"):
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if not isinstance(msg, dict):
            continue
        resp = handle(msg)
        if resp is None:
            continue
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Self-test / probe - neither needs AutoCAD
# ---------------------------------------------------------------------------

def _selftest() -> int:
    print("=== autocad-mcp selftest ===", file=sys.stderr)
    checks = []

    def check(label, cond, extra=""):
        checks.append(bool(cond))
        print(f"  [{'PASS' if cond else 'FAIL'}] {label} {extra}", file=sys.stderr)

    check("tools registered", len(TOOLS) >= 10, f"{len(TOOLS)} tools")
    print("  tools: " + ", ".join(sorted(TOOLS)), file=sys.stderr)

    bad = [n for n in TOOLS if TOOLS[n]["inputSchema"].get("type") != "object"]
    check("all schemas well-formed", not bad, str(bad))

    r = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    check("initialize responds",
          r and r["result"]["serverInfo"]["name"] == "autocad-mcp")
    r = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    check("tools/list matches registry",
          r and len(r["result"]["tools"]) == len(TOOLS))
    r = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "autocad_status", "arguments": {}}})
    text = r["result"]["content"][0]["text"]
    try:
        body = json.loads(text)
    except ValueError:
        body = {"unparsed": text}
    check("autocad_status degrades gracefully",
          "connected" in body or "unparsed" in body, text[:160])
    r = handle({"jsonrpc": "2.0", "id": 4, "method": "nope"})
    check("unknown method -> error", "error" in r)
    r = handle({"jsonrpc": "2.0", "id": 5, "method": "notifications/initialized"})
    check("notification -> no response", r is None)

    ok = all(checks)
    print(f"=== {'ALL PASS' if ok else 'FAILURES PRESENT'} ===", file=sys.stderr)
    return 0 if ok else 1


def _probe() -> int:
    print(json.dumps(_tools_payload(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    if "--probe" in sys.argv:
        sys.exit(_probe())
    serve()

# autocad-mcp（中文说明）

让 WorkBuddy（或任意 MCP 客户端）通过 Windows COM 自动化驱动 AutoCAD —— 画图、读图、改图、跑命令。

仓库：https://github.com/dxlary/autocad-mcp

零第三方依赖（仅 `pywin32`）：MCP 协议层用 Python 标准库自己实现，离线可用，不会因 PyPI 抽风而装不上。

> 本文件是英文 [README.md](README.md) 的中文对照版，内容保持一致。

## 你需要什么

| 要求 | 说明 |
|---|---|
| Windows | COM/ActiveX 仅 Windows 有 |
| 完整版 AutoCAD，**不是 LT** | AutoCAD LT 没有自动化接口 |
| AutoCAD 2018 – 2026 | 通过 ProgID 自动定位 |
| Python 3.10+ | 任意装有 `pywin32` 的解释器 |

AutoCAD 必须已启动并打开图纸。未打开时工具会返回清晰提示，而非崩溃。

## 安装

```bat
pip install pywin32
```

或从 GitHub 安装（同时得到 `autocad-mcp` 命令，配置里直接写 `"command": "autocad-mcp"`）：

```bat
pip install git+https://github.com/dxlary/autocad-mcp.git
```

## 接入 WorkBuddy

把下面内容加进 `%USERPROFILE%\.workbuddy\mcp.json`，把两条路径换成你自己的：

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

然后打开 WorkBuddy 连接器管理页，在自定义连接器里找到 `autocad-mcp` 并点击 **Trust**（手动添加的 MCP 不会自动激活）。

## 不需要 AutoCAD 也能验证

```bat
python server.py --selftest   % 12 项自检，无需 AutoCAD
python server.py --probe      % 打印工具清单
```

## 工具（17 个）

| 工具 | 用途 |
|---|---|
| `autocad_status` | 版本、当前图纸、实体数量 |
| `autocad_connect` | 连接，或 `launch=true` 启动 AutoCAD |
| `autocad_list_layers` | 所有图层（颜色 / 线型 / 状态） |
| `autocad_list_entities` | 模型空间实体，可按图层 / 类型过滤 |
| `autocad_get_extents` | EXTMIN / EXTMAX 包围盒 |
| `autocad_draw_line` | 两点之间画线 |
| `autocad_draw_polyline` | 由扁平坐标列表生成 2D 多段线 |
| `autocad_draw_circle` | 圆心 + 半径画圆 |
| `autocad_draw_text` | 单行文字 |
| `autocad_ensure_layer` | 建图层、设 ACI 颜色、置为当前 |
| `autocad_get_variable` | 读系统变量 |
| `autocad_set_variable` | 写系统变量 |
| `autocad_run_command` | 发送命令字符串或 AutoLISP |
| `autocad_zoom_extents` | 缩放至范围 |
| `autocad_save` | 保存，或另存到路径 |
| `autocad_new_drawing` | 新建图纸（可选基于 .dwt） |
| `autocad_open_drawing` | 按路径打开 DWG / DXF |

## 注意事项

- **颜色仅 ACI 索引色**（1 红 / 2 黄 / 3 绿 / 4 青 / 5 蓝 / 6 品红 / 7 白黑）。ActiveX `Color` 属性无真彩色通道。
- **实心填充**：`AddHatch` 不追加 loop 不填充，`3D Face` 永不填充。实心图形请用 2D SOLID 实体，或用 `autocad_run_command` 以 `._INSERT`/`-IMPORT` 导入 R12（AC1009）DXF。
- **`autocad_run_command` 是异步的**：执行后用 `autocad_status` / `autocad_get_extents` 回查结果。
- **锁定版本**：设 `AUTOCAD_PROGID` 环境变量，例如 `AUTOCAD_PROGID=AutoCAD.Application.24.1` 锁定 2022。
- **AutoCAD 是商业软件**：本项目与 Autodesk 无关，用户自行负责授权合规。

## 许可证

MIT。见 [LICENSE](LICENSE)。

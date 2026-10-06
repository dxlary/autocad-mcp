# 贡献指南 / Contributing

谢谢您对 **autocad-mcp** 感兴趣！本项目用 Python 标准库自己实现了 MCP 协议层，零第三方依赖（仅 `pywin32`），欢迎一起把它做得更稳更好。

> 报 Bug 或提功能需求，请直接用仓库的 Issue 模板（点 **New issue** 会自动出现）。本文件讲「怎么改代码并提交」。

## 开发环境

| 要求 | 说明 |
|---|---|
| Windows | COM / ActiveX 仅 Windows 有 |
| 完整版 AutoCAD（**不是 LT**） | LT 没有自动化接口 |
| Python 3.10+ | 装有 `pywin32` |
| Git | 用于 clone / 提 PR |

```bat
git clone https://github.com/dxlary/autocad-mcp.git
cd autocad-mcp
pip install pywin32
```

把下面内容加进 `%USERPROFILE%\.workbuddy\mcp.json`，把路径换成你自己的，再到 WorkBuddy 连接器管理页面对 `autocad-mcp` 点 **Trust**：

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

## 提交前先验证

```bat
python server.py --selftest   % 应为 ALL PASS（无需打开 AutoCAD）
python server.py --probe      % 打印工具清单，确认 schema 正确
```

## 代码结构

| 模块 | 职责 |
|---|---|
| `acad_core.py` | 工具注册表 + 由函数签名自动生成 JSON Schema |
| `acad_com.py` | COM 桥接层（ProgID 回退链、VARIANT 构造、异常封装） |
| `acad_tools_a.py` / `acad_tools_b.py` | 具体工具实现，导入即注册 |
| `server.py` | 入口：stdio 协议、dispatch、`--selftest` / `--probe` |

**新增一个工具**：在 `acad_tools_*.py` 里写函数并加 `@tool("名字", "描述")` 装饰器即可，schema 会自动生成，无需手改注册表。

## 代码约定

- **不要引入新的第三方依赖。** 这是本项目的核心约束——保持离线可装、不受 PyPI 波动影响。如确有强需求，请先在 Issue 里讨论。
- 工具参数要有清晰的类型注解（函数注解），schema 依赖 `get_type_hints` 推导。
- 涉及 AutoCAD 实体操作时，注意 ACI 颜色、2D SOLID 填充、`autocad_run_command` 异步等已知坑（详见 README）。

## 提交 Pull Request

1. Fork 本仓库，从 `main` 切出特性分支：`git checkout -b my-feature`。
2. 改动代码，确保 `python server.py --selftest` 全部通过。
3. 若改动影响用户，同步更新 `README.md` / `README.zh-CN.md`。
4. 发起 PR，并**用 PR 模板**填写：改了什么、关联哪个 Issue、自测情况。
5. 一个 PR 尽量聚焦一件事，方便 review。

## 许可证

贡献即表示你同意以 **MIT** 许可证发布你的改动。

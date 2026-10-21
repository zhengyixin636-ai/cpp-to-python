# cpp-to-python

> 把 C++ 代码转换成**语义等价、可直接运行**的 Python 代码 —— 面向 AI 编码助手的 Skill。

一个面向 CodeBuddy / Claude Code 等 AI 编码助手的 **Skill**：当你要求「把这段 C++ 转成 Python」时，它会按固定流程完成类型映射、结构重建、惯用法化、差异标注与自动校验，并交付转换报告。

---

## 特性

- **不逐字符翻译**：目标是**语义等价**，输出惯用 Python（`for item in`、f-string、`@dataclass`、`with` 语句），而不是保留 C++ 痕迹。
- **差异显式标注**：任何语义可能变化的地方（整数除法取整方向、拷贝/引用语义、浮点精度、字节序）都会留下 `TODO(CPP2PY-*)` / `NOTE(CPP2PY-NOTE)` 标记，**禁止静默改写**。
- **不可转换点不伪造**：指针算术、模板元编程、内联汇编等会明确标为 `BLOCKER` 并给出人工决策建议，而不是编造一个假的实现。
- **自带校验脚本**：`scripts/validate_conversion.py` 检查 C++ 语法残留、未标注占位、标注统计与行为测试，退出码语义明确（`0` / `1` / `2`）。
- **自带测试**：32 个 `pytest` 用例覆盖校验脚本全部主要路径，行覆盖率 **96%**。

---

## 目录结构

```
cpp-to-python/
├── SKILL.md                          # Skill 主体：触发条件、输入输出契约、10 步执行流程
├── references/
│   ├── type-and-std-mapping.md       # 类型 / 容器 / 标准库 / 第三方库映射表
│   └── syntax-and-idioms.md          # 语法结构、惯用法、边界陷阱 + 端到端示例
├── assets/
│   └── report-template.md            # 转换报告模板（映射决策 / 差异说明 / 待人工确认清单）
├── scripts/
│   └── validate_conversion.py        # 转换结果校验脚本（可独立使用）
└── tests/
    └── test_validate_conversion.py   # 校验脚本的单元测试
```

## 安装

把整个 `cpp-to-python/` 目录复制到你的项目或全局 skill 目录即可：

```bash
# 项目级
cp -r cpp-to-python <你的项目>/.codebuddy/skills/

# 或用户级
cp -r cpp-to-python ~/.codebuddy/skills/
```

## 使用

直接说出你的意图即可触发（命中即加载）：

```text
帮我把下面这段 C++ 转成 Python：<代码>
把这个 C++ 项目的 Vector.h 和 Vector.cpp 移植到 Python
port this C++ to Python
convert this .cpp to .py
```

触发词覆盖中英文（完整清单见 `SKILL.md` 第 1.1 节）。触发后建议同时提供：

| 信息 | 默认值 |
| --- | --- |
| 目标 Python 版本 | 3.10+ |
| 是否允许第三方库 | 允许（`numpy` / `pytest` 等） |
| 是否保留 `main` CLI 行为 | 保留 |
| 性能要求 | 无特殊要求 |

产出包含三部分：**可运行的 Python 模块**（类型注解 + 中文注释）、**转换报告**、以及自动执行校验的结果。

---

## 校验脚本（可独立使用）

```bash
# 基本用法（Windows 建议用 py -3）
py -3 scripts/validate_conversion.py converted.py

# 多文件 + 行为测试
py -3 scripts/validate_conversion.py a.py b.py --tests-cmd "py -3 -m pytest tests -q"

# 结构化输出（供 CI 消费）
py -3 scripts/validate_conversion.py converted.py --json
```

### 退出码

| 码 | 含义 | 处理 |
| --- | --- | --- |
| `0` | 全部通过 | 可交付 |
| `1` | 语法错误 / C++ 残留 / 未标注的 `raise NotImplementedError` / 行为测试失败 | **必须修复** |
| `2` | 仅存在已标注的 `TODO(CPP2PY-BLOCKER)` | 正常结果，在报告「待人工确认清单」中逐条汇总后可交付 |

### 检查项

- Python 语法是否可解析（`compile()`）
- 是否残留 C++ 语法特征（`#include`、`std::`、`new`/`delete`、`cout`、模板语法、宏等）
- `CPP2PY` 标注统计（`TODO(CPP2PY-BLOCKER)` / `TODO(CPP2PY-REVIEW)` / `NOTE(CPP2PY-NOTE)`）
- 是否存在**未标注**的 `raise NotImplementedError` 占位
- 可选：执行外部测试命令做行为验证

> 注：脚本**不检测** `pass` / `...` 空函数体占位，`SKILL.md` 步骤 9 给出了配套的 AST 补检命令。

---

## 开发

```bash
pip install pytest pytest-cov
py -3 -m pytest tests/ --cov=validate_conversion --cov-report=term-missing
```

---

## 标注约定

```python
# TODO(CPP2PY-BLOCKER): <无法转换的原因> — <建议的人工决策/替代方案>
# TODO(CPP2PY-REVIEW):  <已转换但语义可能不等价的原因> — <验证办法>
# NOTE(CPP2PY-NOTE):    <说明性注释，帮助读者理解 C++ 与 Python 的差异>
```

标记必须写在**受影响代码的正上方**；`BLOCKER` 必须给出「建议」部分。

## License

MIT

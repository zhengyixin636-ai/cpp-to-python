---
name: cpp-to-python
description: "将 C++ 代码转换为语义等价、可直接运行的 Python 代码。This skill should be used when the user asks to convert, rewrite, translate, port or migrate C++ code (including .cpp/.cc/.cxx/.h/.hpp sources, algorithms, classes, structs and templates) into Python — 例如「C++ 转 Python」「把这段 C++ 改成 Python」「将 C++ 代码改写/翻译/移植/重写为 Python」「port this C++ to Python」「translate C++ to Python」「convert .cpp to .py」。覆盖类型映射、STL 与标准库替换、类与函数结构重建、内存管理差异处理、异常与边界处理，并对无法自动转换的部分显式标注。"
---

# C++ → Python 转换

## 目的

把 C++ 源码翻译为**语义等价、可直接运行、可读性强**的 Python 代码：保持原有输入输出行为、控制流与数据结构语义，而不是逐字符的机械翻译。翻译结果必须是惯用的 Python（idiomatic Python），保留 C++ 痕迹（如手写索引循环代替 `for item in`、用 `#define` 常量）视为不合格。

## 一、触发条件

### 1.1 触发词（命中任意一条即触发）

| 类别 | 触发词 |
| --- | --- |
| 中文直述 | C++ 转 Python、C++ 转换成 Python、把 C++ 改为 Python、将 C++ 代码改写为 Python、C++ 代码翻译成 Python、C++ 重写为 Python、C++ 代码迁移到 Python、cpp 转 py、把 cpp 改成 py |
| 移植类 | 移植 C++ 到 Python、把 C++ 项目迁到 Python、C++ 程序改写成 Python 版本、用 Python 实现这段 C++ |
| 英文 | convert C++ to Python、translate C++ into Python、port C++ code to Python、rewrite this C++ in Python、C++ to Python converter、convert .cpp/.h to .py、python equivalent of this C++ |
| 对象类 | 把某个 C++ 算法/类/结构体/数据结构/模板/竞赛代码改成 Python、LeetCode C++ 解答改 Python |

### 1.2 适用场景

- 单文件或多文件 C++ 源码（`.cpp` `.cc` `.cxx` `.h` `.hpp` `.hxx`）转 Python 模块/包
- 算法题、数值计算、数据处理、工具类脚本的移植
- C++ 类层次（继承、多态、运算符重载）重建为 Python 类
- 头文件 + 实现文件合并为单个 Python 模块

### 1.3 不触发 / 需说明边界的场景

- 纯 Python → C++（反向）、C 语言转 Python（可参照本 Skill，但需额外处理无类/无 STL 的情况）
- 仅解释 C++ 代码含义、或仅做 C++ 重构 —— 不触发转换流程
- 涉及 CUDA、内联汇编、硬件寄存器、操作系统内核、驱动等强平台绑定代码 —— 触发，但必须按「第五节」标注为不可自动转换

## 二、输入与输出契约

### 2.1 输入

- 一段或多段 C++ 代码（粘贴在对话中，或给出文件路径）
- 可选上下文：目标 Python 版本（默认 3.10+）、是否允许第三方库（默认允许 `numpy`/`pytest` 等常见库）、性能要求、是否需要保留 `main` 入口

输入不完整（只有函数片段、缺少头文件、缺少类型定义）时：**先列出缺失项并给出合理假设，再继续转换**，不要因缺上下文而中止。

### 2.2 输出

1. **Python 代码**：可直接运行的完整模块，包含必要 `import`、`if __name__ == "__main__":` 入口、类型注解（默认加上，便于读者理解）
2. **中文注释**：逐行/逐块解释关键逻辑（该项目默认要求）
3. **转换报告**（使用 `assets/report-template.md` 模板）：映射决策、差异说明、待人工确认项清单、验证结果
4. 若原代码分散在多个文件，按原结构组织为包（`__init__.py` + 各模块），或按用户要求合并

### 2.3 输出质量底线

- 不得残留 `#include`、`std::`、`new`/`delete`、`nullptr`、`malloc`/`sizeof`、`cout <<` 等 C++ 语法
- 不得出现「为了省事」的占位实现（如 `pass` 空函数体、直接 `raise NotImplementedError` 而不标注）
- 每个不可自动转换点必须有 `TODO(CPP2PY-*)` 标注（见第五节）

## 三、执行流程（严格按顺序）

### 步骤 0：确认上下文（30 秒，不必阻塞）

快速确认：Python 版本（默认 3.10+）、第三方库白名单、是否保留 CLI 行为。若用户未说明，直接采用默认值并在报告中记录，不要反复追问。

### 步骤 1：代码解析与结构梳理

- 读取全部输入代码/文件，识别：头文件依赖、命名空间、全局常量与宏、类型定义（`struct`/`class`/`enum`/`typedef`/`using`）、函数与模板、全局变量、`main`
- 画出一份「符号清单」：每个符号的原类型、用途、被引用位置 —— 这是后续类型映射的依据
- 将 `.h` 声明与 `.cpp` 实现**合并**为同一个 Python 定义（声明与实现不分离）
- 判定代码性质：纯算法 / 面向对象 / 系统级（指针算术、内存操作、平台 API）—— 性质决定第 5 步的标注密度

### 步骤 2：依赖与标准库替换

- 按 `references/type-and-std-mapping.md` 把 C++ 标准库替换为 Python 等价物（`vector`→`list`、`map`→`dict`、`unordered_map`→`dict`、`set`→`set`、`sort`→`sorted`/`list.sort` 等）
- 第三方库：`Eigen`/`Armadillo`→`numpy`，`OpenCV`→`opencv-python`（API 基本一致），`Boost`→按具体组件替换或标注
- 无法替换的第三方依赖 → 标注 `TODO(CPP2PY-BLOCKER)` 并给出候选 Python 库建议

### 步骤 3：类型映射

- 按 `references/type-and-std-mapping.md` 的类型表映射：`int`/`long long`→`int`，`double`/`float`→`float`，`std::string`→`str`，`bool`→`bool`，`char`→长度为 1 的 `str`（或按上下文用 `bytes`/`int`）
- **数值语义差异必须处理**：C++ 定宽整型有溢出回绕，Python `int` 任意精度 —— 若原逻辑依赖溢出/位运算/无符号回绕，用掩码（如 `& 0xFFFFFFFF`）显式模拟并加 `NOTE(CPP2PY-NOTE)` 说明
- 整数除法：`int / int` 在 C++ 中是**向零取整**的截断除法。Python 中默认为 `//`，仅在操作数可能为负时改用下面的纯整数辅助函数，以保证大整数下的正确性：
  ```python
  def trunc_div(a: int, b: int) -> int:      # 复刻 C++ int/int 的向零取整语义
      q = abs(a) // abs(b)                   # 先对绝对值做向下取整，全程保持整数运算
      return q if (a < 0) == (b < 0) else -q # 同号为正、异号为负，即向零取整
  ```
  禁止使用 `int(a / b)` / `math.trunc(a / b)`：二者先转 float，当操作数绝对值超过 2**53 时会静默丢精度（如 `int(9007199254740993 / 1)` → `9007199254740992`），超过 float 上界时还会抛 `OverflowError`。

### 步骤 4：结构转换

- 命名空间 → Python 模块/包（或用单个模块 + 前缀命名，不要造空壳类）
- `struct`（纯数据）→ `@dataclass`；`class` → Python 类
- 构造函数与初始化列表 → `__init__`；析构函数 → 优先改成上下文管理器（`__enter__`/`__exit__`），仅在确实需要时用 `__del__`
- 成员函数 → 方法（显式 `self`）；`static` 成员 → 模块级常量或 `@staticmethod`
- 运算符重载 → 魔术方法表（见 `references/syntax-and-idioms.md`）
- 函数重载 → 默认参数 / `functools.singledispatch` / 运行时类型分发
- 模板 → 鸭子类型 + `typing.Generic`/`TypeVar`；模板元编程、SFINAE、`constexpr` 计算 → 标注 `BLOCKER`
- `main` → `if __name__ == "__main__":`，命令行参数用 `argparse` 而非 `sys.argv` 裸解析

### 步骤 5：语句级转换与惯用法化

按 `references/syntax-and-idioms.md` 执行，重点：

- `for (int i = 0; i < n; ++i)` → 优先 `for item in ...` / `enumerate` / `range`，只在确实需要索引时保留 `range`
- 指针/引用传参 → 可变对象原地修改，或改为「返回新值」（**必须在报告中说明调用方需重新赋值**）
- 指针算术、数组退化 → 索引/切片，并标注
- `switch` → `match`（3.10+）或字典分派；注意 C++ 的 fall-through 语义
- `iostream` → `print()` / `input()`；格式化 printf → f-string
- 宏与条件编译 → 常量/函数/配置开关；跨平台分支保留并标注

### 步骤 6：内存管理差异处理

- 删除所有 `new`/`delete`/`malloc`/`free`，改为直接构造对象（Python 自动管理）
- `unique_ptr` → 直接持有；`shared_ptr` → 直接持有（引用计数由 Python 提供）；`weak_ptr` → `weakref` 或标注
- RAII（构造即获取、析构即释放）→ `with` 语句 / `contextlib.contextmanager`
- 深拷贝/浅拷贝语义：C++ 值语义拷贝 → 需要独立副本时显式 `copy.deepcopy` 或 `list(...)`，避免共享引用导致行为差异
- 大数组/性能敏感循环 → 建议 `array` 模块或 `numpy`，并说明

### 步骤 7：异常与边界处理

- `try/catch` → `try/except`（按异常类型映射：`std::runtime_error`→`RuntimeError`、`std::out_of_range`→`IndexError`、`std::invalid_argument`→`ValueError`、`std::bad_alloc`→`MemoryError`）
- C++ 中「不抛异常但会越界/UB」的操作（数组越界、空指针解引用、迭代器失效）→ 在 Python 中显式检查并抛出对应异常，或加 `assert`，并加 `NOTE(CPP2PY-NOTE)` 说明这是新增的防御
- 边界条件清单必须逐项验证：空输入、单元素、负数、0、`INT_MIN/INT_MAX`、重复元素、已排序/逆序输入、超大输入

### 步骤 8：标注不可自动转换部分

统一使用以下标记（**必须写在被影响代码的正上方**）：

| 标记 | 含义 | 处理方式 |
| --- | --- | --- |
| `# TODO(CPP2PY-BLOCKER): <原因> — <建议的人工决策>` | 无法自动转换（语义依赖 C++ 特性/平台/未提供的依赖） | 不伪造实现；给出等价方案建议 |
| `# TODO(CPP2PY-REVIEW): <原因>` | 已转换但语义可能不等价（整数溢出、迭代失效、浮点精度、拷贝语义等） | 说明风险点与验证办法 |
| `# NOTE(CPP2PY-NOTE): <说明>` | 说明性注释，无需人工处理 | 帮助读者理解差异 |

> 注意：文档约定统一写成 `NOTE(CPP2PY-NOTE)`。校验脚本 `scripts/validate_conversion.py` 的 `MARKER_PATTERN` 已同时支持 `NOTE(CPP2PY)` 与 `NOTE(CPP2PY-NOTE)`，二者都会被统计；但为避免歧义，正文一律使用 `NOTE(CPP2PY-NOTE)`。

禁止「静默改写」：任何语义可能变化的地方都必须留标记。

### 步骤 9：验证

1. **语法与残留扫描**（必做）：
   ```bash
   # 脚本位于本 Skill 目录下，必须用绝对路径（或先 cd 到 Skill 目录）；Windows 建议用 py -3
   python "<Skill 目录>/scripts/validate_conversion.py" "<生成的.py>"
   # 一次校验多个文件，并顺带执行等价性测试（对应下面第 2 条）
   py -3 "<Skill 目录>/scripts/validate_conversion.py" a.py b.py --tests-cmd "python -m pytest tests -q"
   # 需要给报告/脚本消费结构化结果时再加 --json
   ```
   该脚本检查：Python 语法是否可解析、是否残留 C++ 语法特征、**统计**所有 `CPP2PY` 标注、以及是否出现未标注的 `raise NotImplementedError`（仅回溯该行向上 3 行）。
   注意：脚本**不检测** `pass` / `...` 空函数体占位（见 2.3），这类静默占位需额外执行 AST 补检：
   ```bash
   python -c "import ast,sys; t=ast.parse(open(sys.argv[1],encoding='utf-8').read()); print([(n.name,n.lineno) for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and len(n.body)==1 and isinstance(n.body[0],ast.Pass)])" <生成的.py>
   ```
   输出非空即为存在空函数体占位，必须补全实现或补 `TODO(CPP2PY-BLOCKER)` 标注。
   退出码含义：`0` 通过；`1` 存在语法错误或 C++ 残留（必须修复）；`2` 无阻断问题但存在 `TODO(CPP2PY-BLOCKER)`（需人工确认）。
2. **行为验证**（尽可能做）：
   - 为纯函数/算法编写等价性测试：用相同输入分别运行 C++ 原程序与 Python 版本，对比输出（推荐 `pytest`）
   - 至少覆盖步骤 7 的边界清单
   - 无法运行 C++ 原程序时，用手工构造的「预期输出」做断言
3. **自查清单**：导入是否齐全、命名是否 Python 化（`snake_case`）、是否有未定义符号、类型注解是否合理

### 步骤 10：交付

按 `assets/report-template.md` 输出转换报告，并附完整 Python 代码。

## 四、转换规则速查

详细规则见 references，SKILL.md 只保留索引：

- 类型、容器、标准库、第三方库映射表 → `references/type-and-std-mapping.md`
- 语法结构、惯用法、内存管理、异常、边界、性能陷阱、端到端示例 → `references/syntax-and-idioms.md`
- 转换报告模板 → `assets/report-template.md`
- 校验脚本 → `scripts/validate_conversion.py`

## 五、约束与异常处理

### 5.1 不支持 / 存在歧义的语法如何反馈

**原则：宁可标注，不可猜测。** 遇到下列任一情况：

- 指针算术、类型双关（union/reinterpret_cast）、 placement new
- 模板元编程、`constexpr` 编译期计算、SFINAE、特化
- 内联汇编、SIMD 内建指令、内存对齐/`#pragma pack`、字节序依赖
- 平台 API（Win32/POSIX/驱动/硬件寄存器）、CUDA、跨进程共享内存
- 宏展开依赖（`#ifdef` 平台分支、X-宏、宏拼接）
- 未提供的自定义头文件或第三方库
- C++ 未定义行为（UB）被当作特性使用（如有符号溢出、越界读、未初始化变量）
- 强实时/确定性析构/确定性内存布局要求

处理方式：

1. 保留一个**最小可运行骨架**，或抛出 `NotImplementedError`（消息里写明原因与建议）—— 无论哪种，都必须在正上方（向上 3 行内，校验脚本的回溯窗口）带 `TODO(CPP2PY-BLOCKER)` 标注，否则按「静默占位」判为退出码 1（见 2.3、步骤 9）。不要伪造结果。
2. 在正上方写 `# TODO(CPP2PY-BLOCKER): <无法转换的原因> — <建议：人工实现 X / 改用 Y 库 / 需要补充 Z 信息>`
3. 在报告的「待人工确认清单」中汇总，说明影响范围

### 5.2 转换结果的验证方式

- 必做：`scripts/validate_conversion.py` 语法与残留扫描，要求退出码为 **0 或 2**：
  - `0` 完全通过；
  - `2` 表示仅存在**已标注**的 `TODO(CPP2PY-BLOCKER)`，须在第 4 节「待人工确认清单」逐条汇总后才可交付（这是含不可转换代码时的正常结果，不是失败）；
  - `1` 表示存在语法错误 / C++ 残留 / 未标注的 `raise NotImplementedError` / `--tests-cmd` 行为测试失败，必须修复后重新校验。
- 强推荐：等价性测试（C++ 与 Python 同输入对比输出），覆盖边界清单
- 无法执行验证时，必须显式声明「未运行验证」，并给出用户可自行执行的命令

### 5.3 转换失败时的提示信息

出现以下情况，停止并输出结构化失败说明（不要给半成品代码）：

- 输入不是 C++ 代码 / 代码严重不完整（缺关键定义且无法合理推断）→ 说明缺失内容，请用户补充
- 核心逻辑完全依赖不可转换特性（如整段是模板元编程或内联汇编）→ 说明「该代码无法自动转换」，给出人工重写思路或建议保留 C++ 并用 `ctypes`/`pybind11` 封装调用
- 依赖未提供且无可替代 → 列出缺失依赖，请用户提供头文件或确认可替换的 Python 库

失败说明统一格式：

```
[转换失败] <一句话原因>
- 失败位置：<文件/函数/行号>
- 具体原因：<说明>
- 已尝试：<做了什么>
- 建议：<下一步怎么做：补充 X / 手动实现 Y / 保留 C++ 并用 pybind11 封装>
```

## 六、调用示例

### 示例 A：单段算法

> 用户：帮我把下面这段 C++ 转 Python（统计词频并排序）

执行：识别 `unordered_map` → `dict`、`sort` 自定义比较器 → `sorted(key=...)`、输出 `cout` → `print`；生成带类型注解与中文注释的 Python 文件；运行 `validate_conversion.py`；报告映射决策（比较器 `> ` 改为 `reverse=True`）。

### 示例 B：多文件类工程

> 用户：把这个 C++ 项目的 `Vector.h` 和 `Vector.cpp` 移植到 Python

执行：合并 `.h`/`.cpp` → 单个 `vector.py`；运算符重载 → `__add__`/`__sub__`/`__mul__`/`__eq__`；析构与 RAII → 上下文管理器；`std::vector<double>` → `list[float]`（性能敏感时建议 `numpy`）；为每个运算符写对比测试；报告列出拷贝语义差异。

### 示例 C：含不可转换部分

> 用户：把这段用指针算术和 `reinterpret_cast` 读二进制文件的 C++ 改成 Python

执行：文件读取 → `open(..., 'rb')` + `struct.unpack`；指针算术部分标注 `# TODO(CPP2PY-BLOCKER): 依赖指针算术与类型双关，需人工确认字节序与对齐`；给出 `struct` 格式串建议；退出码非 0 时先修复 BLOCKER 标注说明再交付。

## 七、交付检查清单

- [ ] 无 C++ 语法残留（脚本扫描通过）
- [ ] 所有函数/类均已实现，无静默占位
- [ ] 整数除法、溢出、无符号语义已显式处理
- [ ] 拷贝/引用语义差异已在报告中说明
- [ ] 边界条件已验证或有明确说明
- [ ] 所有不可转换点带 `TODO(CPP2PY-*)` 标记并汇总到报告
- [ ] 代码为惯用 Python（`snake_case`、类型注解、中文注释）
- [ ] 附转换报告

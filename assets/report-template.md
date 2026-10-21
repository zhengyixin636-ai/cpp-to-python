# C++ → Python 转换报告

> 源文件：`<原文件名/路径>`
> 输出文件：`<生成的 .py 路径>`
> 目标 Python 版本：`3.10+`
> 转换日期：`<YYYY-MM-DD>`

## 1. 转换概述

- 原代码性质：（纯算法 / 面向对象 / 系统级 / 混合）
- 代码规模：`<N>` 个类、`<M>` 个函数、约 `<K>` 行
- 总体结论：（完全等价转换 / 等价转换但有 N 处需人工确认 / 部分无法自动转换）

## 2. 结构与依赖映射

| C++ 符号 / 头文件 | Python 对应 | 说明 |
| --- | --- | --- |
| `#include <vector>` | 内建 `list` | |
| `std::unordered_map` | `dict` / `collections.Counter` | |
| `namespace foo` | 模块 `foo.py` | |
| `struct Bar` | `@dataclass Bar` | |

## 3. 关键语义差异（必读）

| 位置 | C++ 行为 | Python 行为 | 处理方式 |
| --- | --- | --- | --- |
| `divide()` | `int / int` 向零取整 | `//` 向下取整 | 改用 `trunc_div(a, b)`（纯整数，避免大整数浮点精度丢失） |
| `push()` | 值语义拷贝 | 引用共享 | 显式 `list(...)` 拷贝 |

## 4. 待人工确认清单

| 级别 | 位置 | 问题 | 建议 |
| --- | --- | --- | --- |
| BLOCKER | `parse()` L23 | 依赖 `reinterpret_cast` 与结构体内存布局 | 确认字节序，改用 `struct` 显式格式串 |
| REVIEW | `hash_sum()` L40 | 依赖 32 位无符号溢出回绕 | 已加 `& 0xFFFFFFFF` 掩码，请用原程序对比验证 |

## 5. 验证结果

- [x] 语法检查：`python scripts/validate_conversion.py <file>.py` → 通过（退出码 0）
- [x] C++ 残留扫描：无 `std::` / `new` / `#include` 等残留
- [ ] 等价性测试：`<说明是否已对比 C++ 原程序输出；未做则说明原因>`
- 覆盖的边界用例：空输入 / 单元素 / 负数 / 0 / 极大值 / 重复元素 / 已排序输入

测试命令：

```bash
python -m pytest tests/test_<name>.py -v
```

## 6. 使用说明

- 运行：`python <file>.py <args>`
- 新增依赖：`pip install <pkg>`
- 行为变化提醒：`<如：原程序从 argv 读取，现改为 argparse；调用方需把 f(x) 改为 x = f(x)>`

## 7. 未覆盖 / 已知限制

- `<例如：性能较 C++ 下降约 X 倍，建议向量化或保留 C++ 用 pybind11 封装>`
- `<例如：未验证并发场景>`

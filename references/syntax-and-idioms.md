# 语法结构、惯用法、陷阱与端到端示例

## 1. 预处理指令

| C++ | Python |
| --- | --- |
| `#include <iostream>` | `import` 对应模块（见映射表） |
| `#include "Foo.h"` | 合并进同一模块，或用 `from .foo import ...` |
| `#pragma once` / `#ifndef` 守卫 | 不需要（Python 模块自带缓存） |
| `#define N 100` | 模块级常量 `N = 100` |
| `#define MAX(a,b) ((a)>(b)?(a):(b))` | `def max2(a, b): return a if a > b else b`（宏有多次求值副作用，函数更安全，加 `NOTE`） |
| `#define LOG(x) ...` 复杂宏 | 函数；依赖 `#` / `##` 拼接 → `TODO(CPP2PY-BLOCKER)` |
| `#ifdef _WIN32 ... #else ...` | 用 `sys.platform` 或配置常量分支，保留两个分支并 `NOTE` |
| `#if` 编译期开关 | 运行时 `if` 或配置字典 |
| `#pragma pack` / `#pragma once` 之外的 `#pragma` | 多数无对应 → `NOTE(CPP2PY-NOTE)` |

## 2. 命名空间与文件组织

- `namespace ns { ... }` → 包目录 `ns/` + `__init__.py`，或单模块 `ns_utils.py`
- 嵌套命名空间 → 嵌套包
- `using namespace std;` → 删除，直接调用对应 Python 能力
- `using alias = Foo<Bar>;` → 类型别名 `Alias = Foo[Bar]` 或 `Alias = Bar`
- `namespace { ... }`（匿名命名空间，文件内私有）→ 模块级 `_private_name`（下划线前缀）
- `.h` 声明 + `.cpp` 实现 → 合并为一个 `.py`，不要模仿「声明/实现分离」

## 3. 类型定义

- 纯数据 `struct` → `@dataclass`（`@dataclass(slots=True)` 可提升性能）
- 需要不变性 → `@dataclass(frozen=True)`
- 需要默认值 → 字段默认值；可变默认值用 `field(default_factory=list)`
- `struct` 带方法 → 普通 `class`
- 继承 `class D : public B` → `class D(B)`
- 多重继承 → `class D(B1, B2)`（注意 MRO 差异，加 `NOTE`）
- `virtual` + 覆盖 → Python 默认虚派发；`override` 关键字无对应，建议保留同名方法
- 纯虚函数 / 抽象类 → `abc.ABC` + `@abstractmethod`
- `final` / `= delete` → 无直接对应，用 `NOTE` 或 `NotImplementedError`
- 访问控制在 Python 中靠约定：`public` → 直接命名；`protected` → `_name`；`private` → `__name`（名称改写）或 `_name`
- `friend` → 无对应，改为公开方法或模块级函数（`NOTE`）

## 4. 函数与方法

- 构造函数 + 初始化列表 `: a(x), b(y)` → `def __init__(self, x, y): self.a = x; self.b = y`（注意初始化列表顺序 == 声明顺序，Python 中按代码顺序，需保持一致）
- 委托构造函数 → `self.__init__` 调用或默认参数
- 拷贝构造 / 赋值运算符 → `__copy__` 或显式 `copy` 方法
- 析构函数 → 见内存管理（优先 `__exit__`）
- 默认参数 → 直接支持；**可变默认参数必须用 `None` 哨兵**（`def f(x=None): x = x or []` → 更准确：`if x is None: x = []`）
- 函数重载 → 优先级：默认参数 > `functools.singledispatch` > 运行时 `isinstance` 分发
- 引用传参 `void f(int& x)` → 返回新值（`x = f(x)`）或传入可变容器；**必须在报告中提醒调用方改赋值方式**
- 输出参数 `void f(vector<int>& out)` → 返回 `list`
- `const T&` → 正常传参（Python 无法表达不可变约束，用 `NOTE`）
- 内联 `inline` → 不需要
- `static` 成员函数 → `@staticmethod`；`static` 局部变量 → 用可变默认参数或类属性（**易错**，加 `NOTE`）
- `constexpr` 函数 → 普通函数；若用于编译期常量（数组长度、模板参数）→ `TODO(CPP2PY-BLOCKER)`
- 变参模板 / `std::initializer_list` → `*args` / `**kwargs`
- `main(int argc, char** argv)` → `def main() -> int:` + `argparse`，末尾 `if __name__ == "__main__": sys.exit(main())`

## 5. 模板与泛型

| C++ | Python |
| --- | --- |
| `template<typename T> T max(T a, T b)` | 鸭子类型，直接 `def maximum(a, b)`；注解用 `TypeVar` |
| `template<typename T> class Box` | `class Box(Generic[T])` |
| 模板特化 | `functools.singledispatch` 或 `isinstance` 分支 |
| 变参模板 | `*args` |
| SFINAE / `enable_if` / `concepts` | 无对应 → `TODO(CPP2PY-BLOCKER)` 或运行时检查 |
| 模板元编程（编译期计算） | 运行时计算 → `BLOCKER` |
| `if constexpr` | 运行时 `if` + `NOTE` |

## 6. 运算符与魔术方法

| C++ | Python |
| --- | --- |
| `operator+` | `__add__` |
| `operator-`（二元/一元） | `__sub__` / `__neg__` |
| `operator*` / `/` | `__mul__` / `__truediv__`；需 C++ 整型除法语义用 `__floordiv__` |
| `operator%` | `__mod__` |
| `operator==` / `!=` | `__eq__`（`!=` 自动取反，或显式 `__ne__`） |
| `<` `<=` `>` `>=` | `__lt__` `__le__` `__gt__` `__ge__`（推荐 `@dataclass(order=True)` 或 `functools.total_ordering`） |
| `operator[]` | `__getitem__` / `__setitem__` |
| `operator()` | `__call__` |
| `operator<<`（流输出） | `__str__` / `__repr__` |
| `operator>>`（流输入） | `classmethod` 解析函数 |
| `operator++` / `--` | 无对应 → 改用方法 `increment()`（`NOTE`） |
| `operator=` | 不需要（`__eq__` 是比较，赋值是语言机制） |
| `operator->` | 不需要 |
| `operator bool` | `__bool__` |
| `operator new` | 不需要 |
| 隐式转换运算符 | 改为显式方法 |

## 7. 控制流

- `for (int i = 0; i < n; ++i)` → 优先 `for x in seq`；需索引 `for i, x in enumerate(seq)`；仅在数字区间用 `for i in range(n)`
- 倒序 `for (int i = n-1; i >= 0; --i)` → `for i in range(n - 1, -1, -1)` 或 `reversed(range(n))`
- `for (auto& x : v)` → `for x in v`（**注意**：修改元素需 `for i, x in enumerate(v): v[i] = ...`，因为 `x = ...` 不会改原容器）
- `for (auto it = m.begin(); it != m.end(); ++it)` → `for k, v in m.items()`
- `while (cin >> x)` → `for line in sys.stdin:` / `iter(input, sentinel)`
- `do { } while (cond)` → `while True: ...; if not cond: break`
- `switch` → `match ... case`（3.10+）或字典分派；**C++ 的 fall-through 必须显式保留**，否则加 `NOTE`
- `goto` → 重构为函数/循环/异常（复杂 goto → `TODO(CPP2PY-REVIEW)`）
- 三元 `a ? b : c` → `b if a else c`
- 逗号运算符 → 拆成多行
- 逗号分隔声明 `int a, b;` → 两行

## 8. 输入输出

- `std::cout << x << std::endl` → `print(x)`（不要在循环里用 `end='\n'` 之外的刷新；`endl` 的 flush 语义通常不需要）
- `std::cin >> x` → `x = int(input())`（需类型转换并捕获 `ValueError`）
- `printf("%.2f", x)` → `print(f"{x:.2f}")`
- `scanf` → `input().split()` + 转换
- `getline` → `input()` / `sys.stdin.readline().rstrip('\n')`
- `std::setw` / `setprecision` → f-string 格式说明符
- 输出缓冲/性能 → `sys.stdout.write` 或 `'\n'.join(...)`

## 9. 边界与未定义行为（必须逐项检查）

| C++ 行为 | Python 行为 | 处理 |
| --- | --- | --- |
| 数组越界读 → UB | 抛 `IndexError` | 若原代码依赖越界，标 `BLOCKER`；否则补边界检查 |
| 有符号整数溢出 → UB | 静默扩展精度 | 需要回绕时加掩码，否则标 `REVIEW` |
| 除零（整型）→ UB/崩溃 | 抛 `ZeroDivisionError` | 显式检查并映射为 `ValueError`/返回哨兵 |
| 空指针解引用 → UB | `AttributeError`/`TypeError` | 加 `if x is None:` 检查 |
| 迭代器失效（边遍历边插入/删除） | `RuntimeError` 或静默错误 | 遍历副本（`for x in list(v)`）或用推导式重建 |
| 未初始化变量 → UB | `NameError` | 必须初始化 |
| 栈上大数组 → 栈溢出 | 无此限制 | 无需处理 |
| 递归深度 | 默认 1000 限制 | 深递归标 `REVIEW`，或 `sys.setrecursionlimit` |
| `char` 符号性平台相关 | `str` 无此问题 | 字节处理显式用 `bytes` |
| 结构体内存布局/对齐 | 无对应 | `struct` 模块显式指定字节序与对齐，标 `BLOCKER` |

## 10. 性能相关

- 数值密集循环 → `numpy` 向量化；无法向量化时考虑 `numba`/`Cython`，并在报告中建议
- 频繁头部插入/删除 → `collections.deque`
- 频繁字符串拼接 → `list` + `join`
- 大量计数 → `collections.Counter` / `defaultdict(int)`
- 列表推导优于 `append` 循环；生成器用于大数据流
- 需要 `O(1)` 查找 → `set` / `dict`
- Python 循环比 C++ 慢 1~2 个数量级：转换后若性能不达标，**明确告知用户**并给出优化路径（向量化 / 缓存 / 保留 C++ 用 `pybind11` 封装）

## 11. 反模式（转换结果中不允许出现）

- 用 `while i < len(a): ...; i += 1` 遍历 → 改为 `for`
- 用 `range(len(a))` 仅为取元素 → 改为 `enumerate` 或直接迭代
- 用 `# define` 风格常量表 → 改为模块常量
- 用类包裹一堆 `@staticmethod` 模拟命名空间 → 改为模块
- 保留 `temp` / `tmp` / `ret` 等无意义变量名而不重命名
- `except: pass` 吞掉异常
- 用 `dict.get` 替代 C++ 的 `operator[]` 插入语义时忘记默认值差异

---

## 12. 端到端转换示例

### 12.1 算法类（词频统计）

**输入 C++**

```cpp
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <algorithm>

using namespace std;

int main() {
    unordered_map<string, int> freq;       // 词 -> 出现次数
    string word;
    while (cin >> word) {                  // 从标准输入逐个读单词
        freq[word]++;                      // 不存在则默认 0 后自增
    }

    vector<pair<string, int>> items(freq.begin(), freq.end());  // 转为可排序数组
    sort(items.begin(), items.end(), [](const auto& a, const auto& b) {
        if (a.second != b.second) return a.second > b.second;   // 次数降序
        return a.first < b.first;                               // 字典序升序
    });

    for (const auto& [w, c] : items) {
        cout << w << " " << c << endl;
    }
    return 0;
}
```

**输出 Python**

```python
"""词频统计：从标准输入读取单词，按出现次数降序、字典序升序输出。"""

from collections import Counter  # 导入 Counter，用于统计词频
import sys  # 导入 sys，用于读取标准输入


def count_words(text: str) -> Counter[str]:
    """统计文本中各单词的出现次数。"""
    words = text.split()            # 按空白切分，等价于 cin >> word 的循环读取
    return Counter(words)           # 返回词频计数器


def sort_by_freq(freq: Counter[str]) -> list[tuple[str, int]]:
    """按出现次数降序、单词字典序升序排序，返回 (单词, 次数) 列表。"""
    # -c 实现次数降序，w 实现同次数时的字典序升序
    return sorted(freq.items(), key=lambda item: (-item[1], item[0]))


def main() -> int:
    """程序入口：读标准输入、统计、排序、输出结果。"""
    text = sys.stdin.read()                     # 一次性读取全部标准输入
    freq = count_words(text)                    # 统计词频
    for word, count in sort_by_freq(freq):      # 按规则遍历排序结果
        print(f"{word} {count}")                # 等价于 cout << w << " " << c << endl
    return 0                                    # 返回 0 表示正常结束


if __name__ == "__main__":
    sys.exit(main())  # 以 main 的返回值作为进程退出码
```

**决策说明**

- `unordered_map` + `++` → `collections.Counter`
- 自定义比较器 → `sorted(key=lambda item: (-item[1], item[0]))`（用取负代替 `>`，因为 `sorted` 只支持 `key` 升序）
- 结构化绑定 `for (const auto& [w, c] : items)` → `for word, count in ...`
- `while (cin >> word)` → `sys.stdin.read().split()`（**差异**：一次性读入内存，超大输入应改为逐行流式处理，需在报告中注明）

### 12.2 类与运算符重载（dataclass + RAII）

**输入 C++**

```cpp
#include <cmath>
#include <fstream>
#include <stdexcept>
#include <string>

class Vec2 {
public:
    Vec2(double x = 0.0, double y = 0.0) : x_(x), y_(y) {}

    Vec2 operator+(const Vec2& rhs) const { return Vec2(x_ + rhs.x_, y_ + rhs.y_); }
    Vec2 operator*(double s) const { return Vec2(x_ * s, y_ * s); }
    bool operator==(const Vec2& rhs) const { return x_ == rhs.x_ && y_ == rhs.y_; }

    double norm() const { return std::sqrt(x_ * x_ + y_ * y_); }

private:
    double x_, y_;
};

class FileReader {
public:
    explicit FileReader(const std::string& path) : fp_(path) {   // 构造即打开（RAII）
        if (!fp_.is_open()) throw std::runtime_error("cannot open: " + path);
    }
    ~FileReader() { if (fp_.is_open()) fp_.close(); }            // 析构即关闭
    std::string readAll() {                                      // 读取全部内容
        return std::string((std::istreambuf_iterator<char>(fp_)),
                            std::istreambuf_iterator<char>());
    }
private:
    std::ifstream fp_;
};
```

**输出 Python**

```python
"""二维向量与文件读取器的 Python 版本。"""

from __future__ import annotations  # 支持在注解中使用未求值的前向引用

import math  # 导入 math，提供开平方等数学函数
from dataclasses import dataclass  # 导入 dataclass，用于快速定义数据类
from pathlib import Path  # 导入 Path，用于面向对象的文件路径处理


@dataclass(frozen=True)  # frozen=True 表示实例不可变，可自动获得 __hash__
class Vec2:
    """二维向量，支持加法、数乘、相等比较与求模长。"""

    x: float = 0.0  # x 分量，默认 0.0
    y: float = 0.0  # y 分量，默认 0.0

    def __add__(self, rhs: Vec2) -> Vec2:
        """向量加法，对应 C++ 的 operator+。"""
        return Vec2(self.x + rhs.x, self.y + rhs.y)  # 返回新向量，不修改自身

    def __mul__(self, s: float) -> Vec2:
        """数乘，对应 C++ 的 operator*(double)。"""
        return Vec2(self.x * s, self.y * s)  # 返回缩放后的新向量

    def norm(self) -> float:
        """计算向量模长，对应 C++ 的 norm()。"""
        return math.sqrt(self.x * self.x + self.y * self.y)  # 勾股定理求模


class FileReader:
    """文件读取器：用 with 语句保证文件一定被关闭（对应 C++ 的 RAII）。"""

    def __init__(self, path: str | Path) -> None:
        """保存路径；真正的打开动作延迟到 __enter__。"""
        self.path = Path(path)  # 把路径统一转成 Path 对象

    def __enter__(self) -> FileReader:
        """进入 with 代码块时打开文件，对应 C++ 构造函数中的打开逻辑。"""
        # TODO(CPP2PY-REVIEW): C++ 构造失败抛异常，Python 延迟到 with 处才抛，调用点行为一致但时机不同
        self._fp = self.path.open("r", encoding="utf-8")  # 以文本只读模式打开
        return self  # 返回自身，供 with ... as 使用

    def __exit__(self, exc_type, exc, tb) -> None:
        """退出 with 代码块时关闭文件，对应 C++ 析构函数。"""
        self._fp.close()  # 关闭文件句柄

    def read_all(self) -> str:
        """读取文件全部内容。"""
        return self._fp.read()  # 一次性读出全部文本


# 使用方式：with FileReader("a.txt") as r: print(r.read_all())
```

**决策说明**

| C++ | Python | 理由 |
| --- | --- | --- |
| `class Vec2` + 私有成员 | `@dataclass(frozen=True)` | 纯数据类型，自动生成 `__init__`/`__eq__`/`__repr__` |
| `operator==` | `@dataclass` 自动生成 | 无需手写 |
| RAII 构造/析构 | `__enter__` / `__exit__` | Python 析构时机不确定，`with` 提供确定性释放 |
| `throw std::runtime_error` | `open()` 自身抛 `OSError` | 若需保持「错误信息完全一致」，显式捕获并 `raise RuntimeError(...)` |
| `double` | `float` | Python `float` 即双精度 |

### 12.3 含不可自动转换部分（指针算术 + 类型双关 + 模板元编程）

**输入 C++**

```cpp
#include <cstdint>
#include <cstring>

#define MAGIC 0xABCD

template <int N>
struct Factorial { static const int value = N * Factorial<N - 1>::value; };
template <>
struct Factorial<0> { static const int value = 1; };

struct Header { uint16_t magic; uint32_t size; };

int parse(const uint8_t* buf, size_t len) {
    if (len < 6) return -1;
    const Header* h = reinterpret_cast<const Header*>(buf);   // 指针算术 + 类型双关
    if (h->magic != MAGIC) return -2;
    return static_cast<int>(h->size);
}
```

**输出 Python**

```python
"""二进制头部解析：演示不可自动转换部分的标注写法。"""

import struct  # 导入 struct，用于按指定字节序解包二进制数据

MAGIC = 0xABCD          # 对应 C++ 的 #define MAGIC 0xABCD
HEADER_FMT = "<HI"      # 小端序：H=uint16，I=uint32，共 6 字节
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # 计算头部字节数，值为 6


# TODO(CPP2PY-BLOCKER): C++ 模板元编程 Factorial<N> 在编译期求值，Python 无编译期常量机制
# 建议：改为运行时计算，例如 def factorial(n: int) -> int: return math.factorial(n)
# 若该值用作数组长度或模板参数，需人工确认是否可改为运行时求值


def parse(buf: bytes) -> int:
    """解析 buf 前 6 字节的头部，成功返回 size，失败返回负错误码。"""
    if len(buf) < HEADER_SIZE:      # 长度不足，对应 C++ 的 if (len < 6) return -1
        return -1                   # 返回 -1 表示数据不完整

    # TODO(CPP2PY-REVIEW): 原代码用 reinterpret_cast 直接映射结构体内存，依赖
    # 目标平台字节序与对齐（默认小端、无填充）；此处显式指定 '<' 小端、无对齐填充。
    # 若原平台为大端，请把 HEADER_FMT 改为 '>HI'。
    magic, size = struct.unpack_from(HEADER_FMT, buf, 0)  # 从偏移 0 解包两个字段

    if magic != MAGIC:              # magic 校验失败
        return -2                   # 返回 -2 表示魔数不匹配

    return int(size)                # size 为无符号 32 位，转 int 返回
```

**标注要点**

- 模板元编程 → `TODO(CPP2PY-BLOCKER)`，不伪造编译期行为，给出运行时替代方案
- `reinterpret_cast` + 结构体内存布局 → `TODO(CPP2PY-REVIEW)`，说明字节序/对齐假设与修改方法
- `#define MAGIC` → 模块常量（简单宏可安全转换）
- 裸指针 `const uint8_t*` → `bytes`；长度参数 `size_t len` 由 `len(buf)` 取代，从签名中移除

---

## 13. 标注写法速查

```python
# TODO(CPP2PY-BLOCKER): <无法转换的原因> — <建议的人工决策/替代方案>
# TODO(CPP2PY-REVIEW):  <已转换但语义可能不等价的原因> — <验证办法>
# NOTE(CPP2PY-NOTE):    <说明性注释，帮助读者理解 C++ 与 Python 的差异>
```

放置规则：

- 标记写在**受影响代码的正上方**，不要集中在文件末尾
- 一个标记只描述一个问题；同一处多个问题用多行标记
- `BLOCKER` 必须有「建议」部分，否则视为不合格标注
- 报告中必须汇总所有标记，格式为「位置 — 级别 — 说明 — 建议」

# 类型、容器、标准库与第三方库映射表

转换时按本表查表执行。若表格给出多个候选，按「语义优先 > 性能 > 可读性」选择，并在报告中说明选择理由。

## 1. 基础类型映射

| C++ | Python | 说明与陷阱 |
| --- | --- | --- |
| `bool` | `bool` | 注意 C++ 中 `bool` 可隐式转 int，Python 中 `True + 1 == 2` 也成立但语义不同，显式转换更清晰 |
| `char` | `str`（长度 1） | 若用于数值运算 → `int` + `ord()`/`chr()`；若用于字节 → `bytes` |
| `signed char` / `unsigned char` | `int` / `int`（`& 0xFF`） | 无符号回绕需掩码 |
| `short` / `unsigned short` | `int` | 依赖 16 位回绕时加 `& 0xFFFF` |
| `int` / `long` | `int` | Python `int` 任意精度，无溢出 |
| `unsigned int` | `int` + 掩码 | 依赖回绕时加 `& 0xFFFFFFFF` |
| `long long` / `int64_t` | `int` | 同上 |
| `size_t` | `int` | Python 无无符号；负数索引语义不同（`-1` 表示最后一个） |
| `float` / `double` | `float` | Python `float` 即 IEEE754 双精度；`float` 精度差异用 `NOTE(CPP2PY-NOTE)` 标注 |
| `long double` | `float` 或 `decimal.Decimal` | 需更高精度时用 `Decimal` |
| `std::string` | `str` | C++ 可变、Python 不可变 → 频繁拼接改用 `list` + `''.join` 或 `io.StringIO` |
| `std::string_view` | `str`（切片） | 切片会拷贝，超大字符串注意性能 |
| `const char*` | `str` / `bytes` | 二进制数据用 `bytes` |
| `std::wstring` | `str` | Python 3 `str` 即 Unicode |
| `std::complex<double>` | `complex` | 内建类型 |
| `enum` / `enum class` | `enum.Enum` / `enum.IntEnum` | 与整数比较用 `IntEnum`；`IntFlag` 对应位标志 |
| `std::optional<T>` | `T \| None` | 用 `Optional[T]` 注解 |
| `std::variant<A,B>` | `Union[A, B]` | 运行时需 `isinstance` 分发 |
| `std::pair<A,B>` | `tuple[A, B]` | 或 `@dataclass`（需字段名时） |
| `std::tuple<...>` | `tuple` / `NamedTuple` | 需字段名用 `NamedTuple` |
| `std::nullptr_t` / `NULL` | `None` | 判断用 `is None` |
| `void` | `None` | 返回值 |
| `auto` | 不加注解或具体类型 | 尽量补上具体类型注解 |
| `T*`（裸指针） | 对象引用 / `None` | 见「内存管理」章节 |
| `T&`（引用） | 对象引用 | Python 全是引用语义 |
| `std::function<F>` | `Callable[..., R]` | `typing.Callable` |

### 数值语义必查项

- **整数除法**：`a / b`（整型）→ `a // b`；但 C++ 是「向零取整」，`//` 是「向下取整」。负数场景用 `int(a / b)` 或 `math.trunc(a / b)`。
- **取模**：C++ `%` 结果符号与被除数一致，Python 与除数一致 → 负数取模差异需显式处理。
- **溢出回绕**：C++ 定宽整型静默回绕，Python 无限精度。位运算/哈希/校验和/随机数生成等依赖回绕的代码必须加掩码，例如 `x = (x * 1103515245 + 12345) & 0x7FFFFFFF`。
- **无符号比较**：`size_t` 与负数比较在 C++ 中会产生巨大正数 → Python 中需重写判断逻辑。
- **浮点**：`NaN` 传播、`-0.0`、`inf` 行为基本一致，但输出格式需对齐（`f"{x:.6f}"`）。

## 2. STL 容器映射

| C++ | Python | 关键差异 |
| --- | --- | --- |
| `std::vector<T>` | `list[T]` | 需数值计算 → `array.array` / `numpy.ndarray`；需双端操作 → `collections.deque` |
| `std::array<T,N>` | `tuple` 或 `list`（不强制长度） | 需要定长约束时加断言 |
| `std::deque<T>` | `collections.deque` | 支持 `popleft()`/`appendleft()` |
| `std::list<T>` | `list`（通常足够） | 需 O(1) 插入删除节点 → 手写双向链表或用 `blist` 替代方案并标注 |
| `std::forward_list` | `list` / 手写 | 少用 |
| `std::set<T>` | `set[T]` | 有序性需保留时用 `sorted()` 或第三方有序集合并标注 |
| `std::multiset<T>` | `list` + `bisect` 或 `collections.Counter` | 需计数用 `Counter` |
| `std::map<K,V>` | `dict[K,V]`（3.7+ 保序） | 依赖有序遍历时可用 `sorted(d.items())` |
| `std::unordered_map<K,V>` | `dict[K,V]` | 键必须可哈希 → 原键为自定义类型需实现 `__hash__`/`__eq__` |
| `std::unordered_set<T>` | `set[T]` | 同上 |
| `std::multimap` | `dict[K, list[V]]` | |
| `std::stack<T>` | `list`（`append`/`pop`） | 或 `collections.deque` |
| `std::queue<T>` | `collections.deque` | `popleft()` |
| `std::priority_queue<T>` | `heapq`（最小堆） | 最大堆用负值；需自定义比较器时包装成元组 |
| `std::bitset<N>` | `int`（位运算）或 `list[bool]` | 大位集用 `int` 位运算并加掩码 |
| `std::valarray` | `numpy.ndarray` | |
| `std::span<T>` | 切片 / `memoryview` | |

## 3. `<algorithm>` 与常用算法映射

| C++ | Python |
| --- | --- |
| `std::sort(begin, end)` | `list.sort()` / `sorted(iterable)` |
| `std::sort(..., cmp)` | `sorted(x, key=cmp_to_key(cmp))`（`functools`）或改写为 `key` |
| `std::stable_sort` | `sorted()`（Python 排序稳定） |
| `std::find` | `in` / `next((i for i,v in enumerate(x) if ...), -1)` |
| `std::find_if` | `next(filter(pred, x), None)` |
| `std::count` / `count_if` | `sum(1 for v in x if pred(v))` |
| `std::binary_search` | `bisect.bisect_left` + 判断 |
| `std::lower_bound` / `upper_bound` | `bisect.bisect_left` / `bisect.bisect_right` |
| `std::min_element` / `max_element` | `min()` / `max()`（可带 `key=`）；要索引用 `min(range(n), key=...)` |
| `std::minmax_element` | `min()` + `max()` |
| `std::reverse` | `reversed()` / `list.reverse()` / `x[::-1]` |
| `std::rotate` | `collections.deque.rotate` 或切片拼接 |
| `std::unique` | 手写去重（`itertools.groupby` 或有序去重循环） |
| `std::accumulate` | `sum()` / `functools.reduce()` |
| `std::transform` | 列表推导 / `map()` |
| `std::copy` / `copy_if` | 切片 / 列表推导 |
| `std::fill` | `[v] * n`（注意可变对象的共享引用问题） |
| `std::for_each` | `for` 循环（不要用 `map` 产生副作用） |
| `std::any_of` / `all_of` / `none_of` | `any()` / `all()` / `not any()` |
| `std::next_permutation` | `itertools.permutations`（或手写下一个排列） |
| `std::max_element` + 索引 | `max(range(len(x)), key=x.__getitem__)` |
| `std::shuffle` | `random.shuffle()` |
| `std::iota` | `range()` / `list(range(n))` |

## 4. 标准库模块映射

| C++ 头文件 | Python |
| --- | --- |
| `<iostream>` / `<iomanip>` | `print()` / `input()` / f-string 格式化（`f"{x:.3f}"`、`f"{x:>10}"`） |
| `<fstream>` | `open()` / `pathlib.Path.read_text()` |
| `<sstream>` | `io.StringIO` / `str.split()` |
| `<string>` | `str` 方法、`str.encode()` / `bytes.decode()` |
| `<vector>` `<map>` `<set>` | 见容器表 |
| `<algorithm>` `<numeric>` | 见算法表 |
| `<cmath>` | `math` / `cmath`（复数） |
| `<random>` | `random` / `numpy.random`（需可复现时显式传 `seed`） |
| `<chrono>` | `time` / `datetime` / `time.perf_counter()` |
| `<thread>` `<mutex>` `<atomic>` | `threading` / `concurrent.futures.ThreadPoolExecutor` / `queue.Queue`；CPU 密集用 `multiprocessing`；原子性依赖 GIL，需显式 `Lock` |
| `<future>` / `<condition_variable>` | `concurrent.futures.Future` / `threading.Condition` |
| `<regex>` | `re`（注意：C++ 默认 ECMAScript 语法，语法细节需核对） |
| `<filesystem>` | `pathlib` / `os` / `shutil` |
| `<memory>` | 见内存管理章节 |
| `<functional>` | `functools` / `operator` / `lambda` |
| `<limits>` | `math.inf` / `sys.float_info` / `float('inf')` |
| `<cstring>` `<cstdlib>` | `bytes` 方法 / `os` / `sys` |
| `<bitset>` | `int` 位运算 |
| `<queue>` | `queue` / `heapq` / `collections.deque` |
| `<iterator>` | 迭代器协议 / `itertools` |
| `<type_traits>` | 不适用于 Python（鸭子类型），标注 `BLOCKER` |
| `<charconv>` / `atoi` / `stoi` | `int()` / `float()`（带 `try/except ValueError`） |
| `<cassert>` | `assert`（注意：`assert` 在 `-O` 模式下被移除，关键校验用显式 `raise`） |
| `<stdexcept>` | 见异常映射表 |
| `<optional>` `<variant>` | 见类型表 |
| `<format>` (C++20) | f-string / `str.format()` |

## 5. 第三方库映射

| C++ 库 | Python 替代 | 备注 |
| --- | --- | --- |
| Eigen / Armadillo / Blitz++ | `numpy`（+ `scipy.linalg`） | 矩阵运算语义接近 |
| OpenCV (C++) | `opencv-python` | API 基本一致，`Mat` → `numpy.ndarray` |
| Boost.Asio | `asyncio` | 模型不同，需重写 |
| Boost.Filesystem | `pathlib` | |
| Boost.Regex | `re` | 语法需核对 |
| Boost.Thread | `threading` / `concurrent.futures` | |
| Boost.Program_options | `argparse` | |
| Boost.Test / GoogleTest | `pytest` / `unittest` | |
| Qt | `PyQt5/6` / `PySide6` | UI 代码可 1:1 迁移，信号槽需改写 |
| protobuf | `protobuf` (python) | |
| spdlog / log4cxx | `logging` | |
| nlohmann::json | `json` | |
| fmt | f-string / `str.format()` | |
| TensorFlow/PyTorch C++ | 同名 Python 包 | |
| 无对应库 | — | 标注 `TODO(CPP2PY-BLOCKER)` 并列举候选 |

## 6. 内存管理差异

| C++ 概念 | Python 处理 |
| --- | --- |
| `new T` / `delete` / `delete[]` | 直接 `T()`；删除全部 `delete` |
| `malloc` / `free` / `calloc` / `realloc` | `bytearray` / `array.array` / `list`；内存映射用 `mmap` |
| `std::unique_ptr<T>` | 直接持有对象引用 |
| `std::shared_ptr<T>` | 直接持有（Python 引用计数） |
| `std::weak_ptr<T>` | `weakref.ref`（仅对支持弱引用的类型）或标注 |
| `std::make_shared` / `make_unique` | 构造函数调用 |
| RAII（构造获取/析构释放） | `with` 语句；自定义类实现 `__enter__`/`__exit__`，或用 `@contextlib.contextmanager` |
| 析构函数 `~T()` | 优先改 `__exit__`（确定性）；`__del__` 调用时机不确定，仅作兜底 |
| 值语义拷贝（`vector<int> b = a;`） | `b = list(a)` / `a.copy()`；嵌套结构用 `copy.deepcopy` |
| 移动语义 `std::move` | 通常无需处理；大对象转移可用切片清空 |
| 循环引用 | Python 有 GC，但建议用 `weakref` 或显式断开 |
| 对象池 / 自定义 allocator | 通常不需要；性能敏感时标注 |
| 确定性内存布局 / `sizeof` | `struct` / `ctypes.sizeof` / `numpy` dtype；标注 `BLOCKER`（结构体对齐） |

## 7. 异常映射

| C++ | Python |
| --- | --- |
| `std::runtime_error` | `RuntimeError` |
| `std::logic_error` | `ValueError` / `RuntimeError`（按场景） |
| `std::invalid_argument` | `ValueError` |
| `std::domain_error` | `ValueError` |
| `std::length_error` | `ValueError` / `OverflowError` |
| `std::out_of_range` | `IndexError` / `KeyError` |
| `std::overflow_error` | `OverflowError` |
| `std::bad_alloc` | `MemoryError` |
| `std::bad_cast` | `TypeError` |
| `std::system_error` | `OSError`（带 `errno`） |
| `throw;`（重新抛出） | `raise` |
| `noexcept` | 无直接对应；用文档说明或 `NOTE(CPP2PY-NOTE)` |
| `catch (...)` | `except Exception:`（尽量收窄） |
| 未捕获异常 → `terminate` | Python 传播到顶层并打印 traceback |

## 8. 命名与风格

| C++ | Python |
| --- | --- |
| `camelCase` 变量 / 函数 | `snake_case` |
| `PascalCase` 类 / `struct` | `PascalCase`（保持） |
| `kConstant` / `CONSTANT` / `ALL_CAPS` | 模块级 `UPPER_SNAKE_CASE` |
| `m_member` / `member_` | `member`（或用 `_member` 表示私有） |
| `snake_case`（部分代码库） | 保持不变 |
| 头文件 `Foo.h` | `foo.py` |
| 命名空间 `ns::sub` | 包 `ns/sub/` 或模块前缀 |

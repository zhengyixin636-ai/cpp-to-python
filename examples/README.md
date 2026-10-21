# cpp-to-python

把 C++ 代码转换为语义等价、可直接运行的 Python 代码。本仓库以「科澜 VpCore Meta 二进制读写」工程为例，展示了一次完整的转换。

## 目录结构

```
cpp-to-python/
├── cpp_src/        # 原始 C++ 源码（转换前的对照参考）
│   ├── EditMetaDlg.cpp/.h   # 核心逻辑：二进制读写 Meta 文件、对话框交互
│   ├── Util.cpp/.h          # 路径/字符串辅助函数
│   ├── EditMeta.cpp/.h      # MFC 应用程序入口
│   └── ReadMe.txt           # 原始工程说明
├── python/         # 转换后的 Python 代码（每行都带中文注释）
│   └── edit_meta.py         # EditMeta 的 Python 复刻版（含命令行 + 图形界面）
├── data/           # 测试数据
│   └── HZ.meta                # 二进制 Meta 样例（211 字节）
└── README.md
```

## C++ → Python 对应关系

| C++（原始） | Python（转换后） | 说明 |
|---|---|---|
| `fread` / `fwrite` 顺序读写二进制 | `struct.Struct` + `_Reader` 顺序读取器 | 用 `struct` 按小端格式精确读写 |
| `long` / `int`（4 字节） | `struct.Struct("<i")` | MSVC 下 `long` 为 4 字节 |
| `double[4]` / `double[2]` | `struct.Struct("<4d")` / `"<2d"` | 连续多个 `double` |
| `ResolutionInfo` 结构体 | `ResolutionInfo` 数据类 | 保留 64 字节原始数据以兼容填充位 |
| `CEditMetaDlg` 对话框（MFC） | `EditMetaApp`（tkinter） | 用标准库 tkinter 还原界面 |
| `WriteLog` 追加写 txt | `write_log` | 解析时把字段逐行追加写入同名 `.txt` |
| `OnBnClickedEditmeta` / `OnBnClickedIntometa` | `load` / `save_meta` | 解析与写回两个动作 |

## 二进制布局（小端，MSVC 默认对齐）

```
int32   nameLen
char[nameLen]     工程名，含结尾 '\0'
int32   editLayer  最高层级
double  bbox[4]    切割范围 xLeft, yBottom, xRight, yTop
double  origin[2]  原点坐标 xLeft, yTop
int32   xCount
int32   yCount
int32   demCount
  循环 demCount 次：int32 structSize(=64) + 64 字节 ResolutionInfo
int32   domCount
  循环 domCount 次：int32 structSize(=64) + 64 字节 ResolutionInfo
```

## 使用

```powershell
# 直接打开图形界面
python python/edit_meta.py

# 打开界面并载入文件
python python/edit_meta.py data/HZ.meta

# 命令行打印解析结果（不开界面）
python python/edit_meta.py data/HZ.meta --dump

# 不改内容，原样复制一份
python python/edit_meta.py data/HZ.meta -o data/HZ2.meta
```

> 说明：DEM 的 `col/row` 在样例文件中是未初始化内存值 `-842150451`（即 `0xCDCDCDCD`），
> Python 版如实保留该值，与 C++ 原程序行为一致。

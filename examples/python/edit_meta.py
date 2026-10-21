# -*- coding: utf-8 -*-  # 声明文件使用 UTF-8 编码，避免中文乱码
"""Python 复刻版 EditMeta —— 对应 C++ 工程 EditMeta（科澜 VpCore Meta 二进制读写）。

原始 C++ 行为：
    1. 解析 Data/HZ.meta，把每个字段逐行追加写入 Data/HZ.txt；
    2. 把字段填进对话框，供人工修改；
    3. 点击“生成 Meta”，把修改后的结构体原样写回 Data/HZ2.meta。

本脚本完整复刻这三步，并额外提供命令行模式。

二进制布局（小端，MSVC 默认对齐）：
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

ResolutionInfo（64 字节，偏移相对结构体首字节）：
    0   double res
    8   int32  lyr
    12  4 字节对齐填充（原文件中为未初始化内存 0xCDCDCDCD）
    16  double bBox[4]
    48  int32  countSpan[0]
    52  int32  countSpan[1]
    56  bool   isNeedTiler
    57  7 字节尾部填充

用法：
    python edit_meta.py                 # 直接打开界面
    python edit_meta.py HZ.meta         # 打开界面并载入文件
    python edit_meta.py HZ.meta --dump  # 命令行打印字段，不开界面
    python edit_meta.py HZ.meta -o HZ2.meta  # 不改内容，原样复制一份
"""

from __future__ import annotations  # 允许使用 Python 3.10+ 的新类型写法（如 list[int]）

import argparse  # 用来解析命令行参数
import copy  # 提供深拷贝，复制对象时不共享内部数据
import struct  # 负责按指定字节序打包/解包二进制数据
import sys  # 访问命令行参数与标准输入输出
import tkinter as tk  # Python 标准 GUI 库（对应 MFC 的对话框）
from dataclasses import dataclass, field  # 用装饰器快速定义数据类
from pathlib import Path  # 面向对象的文件路径处理
from tkinter import filedialog, messagebox, ttk  # 文件选择框、消息框、主题控件

# ---------------------------------------------------------------- 二进制布局 --

LONG = struct.Struct("<i")  # 定义一个“小端 4 字节有符号整数”的格式（对应 C++ 的 int/long）
DOUBLE4 = struct.Struct("<4d")  # 小端连续 4 个 double（对应 double[4]）
DOUBLE2 = struct.Struct("<2d")  # 小端连续 2 个 double（对应 double[2]）
INT2 = struct.Struct("<2i")  # 小端连续 2 个 int（对应 xCount,yCount）

RESINFO_SIZE = 64  # ResolutionInfo 结构体固定 64 字节
RESINFO = struct.Struct("<di4x4d2i?7x")  # 仅用于校验：double+int+4填充+4double+2int+bool+7填充

OFF_RES = 0  # res 字段在结构体中的起始偏移（double，8 字节）
OFF_LYR = 8  # lyr 字段偏移（int32，4 字节）
OFF_BBOX = 16  # bBox[4] 起始偏移（4 个 double，32 字节）
OFF_COUNT = 48  # countSpan[2] 起始偏移（2 个 int32）
OFF_TILER = 56  # isNeedTiler 字段偏移（bool，1 字节）

# 在结构体中真正会被界面修改的字段偏移与长度（相对结构体首字节）
EDITABLE = ((OFF_RES, 8), (OFF_LYR, 4), (OFF_BBOX, 32), (OFF_COUNT, 8))


class MetaFormatError(ValueError):
    """二进制格式不合法时抛出的自定义异常（继承自 ValueError）。"""


@dataclass  # 自动生成 __init__/__repr__ 等样板代码的数据类
class ResolutionInfo:
    res: float  # 分辨率数值（对应 C++ ResolutionInfo.res）
    layer: int  # 目标层级（对应 lyr）
    bbox: list[float]  # 四至范围 [xLeft, yBottom, xRight, yTop]（对应 bBox[4]）
    counts: list[int]  # 瓦片列数、行数（对应 countSpan[2]）
    need_tiler: bool = False  # 是否需要切片（对应 isNeedTiler）
    raw: bytes = b""  # 原始 64 字节，用于保留填充位（C++ 直接按内存读写，会保留填充）

    @classmethod  # 标记为类方法，第一个参数是类本身而非实例
    def parse(cls, payload: bytes) -> "ResolutionInfo":
        if len(payload) != RESINFO_SIZE:  # 防御：长度不对直接报错
            raise MetaFormatError(f"ResolutionInfo 长度应为 {RESINFO_SIZE}，实际 {len(payload)}")
        res = struct.unpack_from("<d", payload, OFF_RES)[0]  # 从偏移 0 读一个 double
        layer = struct.unpack_from("<i", payload, OFF_LYR)[0]  # 从偏移 8 读一个 int32
        bbox = list(struct.unpack_from("<4d", payload, OFF_BBOX))  # 从偏移 16 读 4 个 double
        counts = list(struct.unpack_from("<2i", payload, OFF_COUNT))  # 从偏移 48 读 2 个 int32
        need_tiler = payload[OFF_TILER] != 0  # 偏移 56 处 1 字节非 0 即视为 True
        return cls(res, layer, bbox, counts, need_tiler, bytes(payload))  # 构造对象，同时保留原始字节

    def pack(self) -> bytes:
        """重建 64 字节；未编辑的填充位沿用原文件内容。"""
        if len(self.raw) == RESINFO_SIZE:  # 如果有原始字节，以它为基础
            buf = bytearray(self.raw)  # 转成可变字节数组，方便按偏移改写
        else:
            buf = bytearray(RESINFO_SIZE)  # 否则用 64 个 0 填充
        struct.pack_into("<d", buf, OFF_RES, float(self.res))  # 写回 res
        struct.pack_into("<i", buf, OFF_LYR, int(self.layer))  # 写回 layer
        struct.pack_into("<4d", buf, OFF_BBOX, *[float(v) for v in self.bbox])  # 写回 4 个 bbox
        struct.pack_into("<2i", buf, OFF_COUNT, *[int(v) for v in self.counts])  # 写回 2 个 count
        buf[OFF_TILER] = 1 if self.need_tiler else 0  # 写回 bool（1 字节）
        return bytes(buf)  # 返回不可变字节串

    def to_row(self) -> list[str]:
        # 把字段拼成一行字符串，格式与 C++ 的 WriteLog 输出一致
        return [f"{self.res:g}", f"{self.layer}", *[f"{v:g}" for v in self.bbox],
                f"{self.counts[0]}", f"{self.counts[1]}", f"{int(self.need_tiler)}"]


@dataclass  # 整个 Meta 文件的顶层数据类
class MetaData:
    project_name: str  # 工程名（对应 m_projectName）
    name_len: int  # 工程名长度（对应 m_ProjectNameLen）
    edit_layer: int  # 最高层级（对应 m_EdLyr）
    bbox: list[float]  # 切割范围（对应 m_BBox[4]）
    origin: list[float]  # 原点坐标（对应 m_orgintCoord[2]）
    x_count: int  # X 方向边数（对应 m_XCount）
    y_count: int  # Y 方向边数（对应 m_YCount）
    dem: list[ResolutionInfo] = field(default_factory=list)  # DEM 分辨率列表（对应 DEMresInfo）
    dom: list[ResolutionInfo] = field(default_factory=list)  # DOM 分辨率列表（对应 DOMresInfo）


# ------------------------------------------------------------------ 读取解析 --

class _Reader:
    # 一个简单的顺序字节读取器，模拟 C++ 用 fread 不断往后读文件
    def __init__(self, data: bytes) -> None:
        self.data = data  # 整个文件的字节内容
        self.pos = 0  # 当前读取位置（指针）

    def take(self, size: int) -> bytes:
        end = self.pos + size  # 计算本次读取的结束位置
        if end > len(self.data):  # 防越界：剩余字节不够
            raise MetaFormatError(
                f"数据不完整：偏移 {self.pos} 处需要 {size} 字节，实际仅剩 {len(self.data) - self.pos} 字节"
            )
        chunk = self.data[self.pos:end]  # 切出本次要读的字节
        self.pos = end  # 指针后移
        return chunk  # 返回切出的字节

    def i32(self) -> int:
        return LONG.unpack(self.take(LONG.size))[0]  # 读 4 字节并解析成 int

    def at_end(self) -> bool:
        return self.pos >= len(self.data)  # 是否读到了文件末尾


def _decode_name(raw: bytes) -> str:
    raw = raw.split(b"\0", 1)[0]  # 以第一个 '\0' 截断，去掉 C 风格字符串结尾
    for encoding in ("gbk", "utf-8"):  # 先试 GBK（中文 Windows 常见），再试 UTF-8
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue  # 解码失败就换下一种编码
    return raw.decode("latin-1", errors="replace")  # 兜底用 latin-1，保证不抛异常


def _encode_name(name: str, name_len: int) -> bytes:
    try:
        raw = name.encode("gbk")  # 尝试用 GBK 编码（与 C++ 程序一致）
    except UnicodeEncodeError:
        raw = name.encode("utf-8")  # 含生僻字时退而求其次用 UTF-8
    raw = raw[:name_len] if name_len > 0 else raw  # 超过 nameLen 就截断
    return raw.ljust(name_len, b"\0")  # 右侧补 '\0' 到 nameLen 长度，对齐 C++ 内存布局


def read_meta(path: Path) -> MetaData:
    reader = _Reader(path.read_bytes())  # 把整个 .meta 文件读成字节并交给读取器
    name_len = reader.i32()  # 先读 4 字节：工程名长度
    if name_len < 0 or name_len > 1 << 20:  # 防御：长度异常（>1MB）视作文件损坏
        raise MetaFormatError(f"非法的工程名长度：{name_len}")
    name_raw = reader.take(name_len)  # 再读 name_len 字节：工程名本身
    meta = MetaData(  # 构造顶层数据对象
        project_name=_decode_name(name_raw),  # 解码工程名
        name_len=name_len,  # 保存长度
        edit_layer=reader.i32(),  # 读最高层级（int32）
        bbox=list(DOUBLE4.unpack(reader.take(DOUBLE4.size))),  # 读 4 个 double：切割范围
        origin=list(DOUBLE2.unpack(reader.take(DOUBLE2.size))),  # 读 2 个 double：原点坐标
        x_count=0,  # 先占位，下面再读
        y_count=0,  # 先占位，下面再读
    )
    meta.x_count, meta.y_count = INT2.unpack(reader.take(INT2.size))  # 读 X/Y 边数
    for target in ("dem", "dom"):  # 依次处理 DEM 与 DOM 两组分辨率
        count = reader.i32()  # 读该组结构体个数
        items = []  # 临时存放本组解析结果
        for index in range(count):  # 循环读取每个 ResolutionInfo
            size = reader.i32()  # 读结构体长度（应为 64）
            if size != RESINFO_SIZE:  # 防御：长度不符说明格式不兼容
                raise MetaFormatError(
                    f"{target.upper()}[{index}] 结构体长度为 {size}，预期 {RESINFO_SIZE}"
                )
            items.append(ResolutionInfo.parse(reader.take(size)))  # 解析并追加
        setattr(meta, target, items)  # 把解析好的列表挂到 meta.dem / meta.dom
    if not reader.at_end():  # 读完后若还有剩余字节，说明解析有遗漏
        raise MetaFormatError(f"文件末尾多出 {len(reader.data) - reader.pos} 字节未解析")
    return meta  # 返回完整的 MetaData


# ------------------------------------------------------------------ 写回输出 --

def write_meta(path: Path, meta: MetaData) -> None:
    name_raw = _encode_name(meta.project_name, meta.name_len)  # 工程名编码成字节
    out = bytearray()  # 用可变字节数组累积输出
    out += LONG.pack(len(name_raw))  # 写入工程名长度
    out += name_raw  # 写入工程名字节
    out += LONG.pack(int(meta.edit_layer))  # 写入最高层级
    out += DOUBLE4.pack(*[float(v) for v in meta.bbox])  # 写入 4 个 double 切割范围
    out += DOUBLE2.pack(*[float(v) for v in meta.origin])  # 写入 2 个 double 原点坐标
    out += INT2.pack(int(meta.x_count), int(meta.y_count))  # 写入 X/Y 边数
    out += LONG.pack(len(meta.dem))  # 写入 DEM 个数
    for item in meta.dem:  # 逐个写 DEM 结构体
        payload = item.pack()  # 先打包成 64 字节
        out += LONG.pack(len(payload))  # 写入结构体长度
        out += payload  # 写入结构体内容
    out += LONG.pack(len(meta.dom))  # 写入 DOM 个数
    for item in meta.dom:  # 逐个写 DOM 结构体
        payload = item.pack()
        out += LONG.pack(len(payload))
        out += payload
    path.write_bytes(bytes(out))  # 一次性写回文件


def log_lines(meta: MetaData) -> list[str]:
    """复刻 C++ 端 WriteLog 的逐行输出顺序。"""
    lines = [f"{meta.name_len}", meta.project_name, f"{meta.edit_layer}"]  # 前 3 行：长度、名字、层级
    lines += [f"{v:g}" for v in meta.bbox]  # 切割范围 4 行
    lines += [f"{v:g}" for v in meta.origin]  # 原点坐标 2 行
    lines += [f"{meta.x_count}", f"{meta.y_count}"]  # X/Y 边数 2 行
    lines.append(f"{len(meta.dem)}")  # DEM 个数 1 行
    for item in meta.dem:  # 每个 DEM：长度 + 字段
        lines.append(f"{RESINFO_SIZE}")  # 结构体长度行
        lines += item.to_row()  # 该结构体各字段行
    lines.append(f"{len(meta.dom)}")  # DOM 个数 1 行
    for item in meta.dom:  # 每个 DOM：长度 + 字段
        lines.append(f"{RESINFO_SIZE}")
        lines += item.to_row()
    return lines  # 返回所有行


def write_log(path: Path, meta: MetaData) -> None:
    """C++ 用追加模式写 HZ.txt，这里保持一致。"""
    with path.open("a", encoding="gbk", errors="replace", newline="\n") as handle:  # 以 GBK 追加方式打开
        for line in log_lines(meta):  # 逐行写入
            handle.write(line + "\n")


def dump_text(meta: MetaData) -> str:
    # 把解析结果整理成给人看的文本（对应界面上的字段显示）
    lines = [
        f"工程名    : {meta.project_name} (nameLen={meta.name_len})",
        f"最高层级  : {meta.edit_layer}",
        f"切割范围  : xLeft={meta.bbox[0]:g} yBottom={meta.bbox[1]:g} "
        f"xRight={meta.bbox[2]:g} yTop={meta.bbox[3]:g}",
        f"原点坐标  : xLeft={meta.origin[0]:g} yTop={meta.origin[1]:g}",
        f"边数      : xCount={meta.x_count} yCount={meta.y_count}",
    ]
    for label, items in (("DEM", meta.dem), ("DOM", meta.dom)):  # 分别打印 DEM/DOM
        for index, item in enumerate(items, start=1):
            lines.append(
                f"{label}[{index}]  : res={item.res:g} lyr={item.layer} "
                f"bbox={item.bbox} col={item.counts[0]} row={item.counts[1]} "
                f"needTiler={int(item.need_tiler)}"
            )
    return "\n".join(lines)  # 合并成一个字符串返回


# -------------------------------------------------------------------- 界面 --

# 界面分组字段定义：每组是 [(标签, 内部键名), ...]，下面 _group 据此生成输入框
FIELDS_BBOX = [("X 左", "bbox0"), ("Y 下", "bbox1"), ("X 右", "bbox2"), ("Y 上", "bbox3")]
FIELDS_ORIGIN = [("X 左", "origin0"), ("Y 上", "origin1"), ("X 边", "xcount"), ("Y 边", "ycount")]
FIELDS_DEM = [("分辨率", "dem_res"), ("目标层", "dem_lyr"), ("X 左", "dem_b0"), ("Y 下", "dem_b1"),
              ("X 右", "dem_b2"), ("Y 上", "dem_b3"), ("Col", "dem_c0"), ("Row", "dem_c1")]
FIELDS_DOM = [("分辨率", "dom_res"), ("目标层", "dom_lyr"), ("X 左", "dom_b0"), ("Y 下", "dom_b1"),
              ("X 右", "dom_b2"), ("Y 上", "dom_b3"), ("Col", "dom_c0"), ("Row", "dom_c1")]


class EditMetaApp(tk.Tk):
    # 主窗口，对应 C++ 的 CEditMetaDlg 对话框
    def __init__(self, initial: Path | None = None) -> None:
        super().__init__()  # 调用父类 Tk 的初始化
        self.title("EditMeta - Python 复刻版")  # 设置窗口标题
        self.resizable(False, False)  # 禁止改变窗口大小
        self.meta: MetaData | None = None  # 当前加载的元数据（初始为空）
        self.source_path: Path | None = None  # 当前打开的文件路径
        self.entries: dict[str, tk.Entry] = {}  # 键名 -> 输入框控件 的映射
        self._build()  # 搭建界面
        if initial:  # 若命令行传入了文件，则自动载入
            self.load(initial)

    # --- 界面搭建
    def _build(self) -> None:
        root = ttk.Frame(self, padding=10)  # 主容器，内边距 10
        root.grid(sticky="nsew")  # 用网格布局铺满
        self.path_var = tk.StringVar(value="未选择文件")  # 顶部显示文件路径的变量
        ttk.Label(root, textvariable=self.path_var, width=72).grid(  # 显示路径的标签
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))  # 占满首行
        self._group(root, "切割范围 BBox", FIELDS_BBOX, 1, 0)  # 第 1 列放 BBox 组
        self._group(root, "原点坐标 / 边数", FIELDS_ORIGIN, 1, 1)  # 第 2 列放原点/边数组
        self._group(root, "DEM 分辨率", FIELDS_DEM, 1, 2)  # 第 3 列放 DEM 组
        self._group(root, "DOM 分辨率", FIELDS_DOM, 1, 3)  # 第 4 列放 DOM 组
        bar = ttk.Frame(root)  # 底部按钮栏容器
        bar.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(12, 0))  # 占第二行
        for text, command in (("解析 Meta", self.pick_and_load),
                              ("写入 Meta", self.save_meta),
                              ("退出", self.destroy)):  # 三个按钮
            ttk.Button(bar, text=text, command=command).pack(side="left", padx=4)  # 横向排列

    def _group(self, parent: ttk.Frame, title: str, fields, row: int, column: int) -> None:
        frame = ttk.LabelFrame(parent, text=title, padding=8)  # 带标题的边框分组
        frame.grid(row=row, column=column, padx=4, sticky="n")  # 放在指定网格位置
        for index, (label, key) in enumerate(fields):  # 遍历字段生成标签+输入框
            ttk.Label(frame, text=f"{label}：").grid(row=index, column=0, sticky="e", pady=2)  # 标签右对齐
            entry = ttk.Entry(frame, width=14)  # 单行输入框
            entry.grid(row=index, column=1, pady=2)  # 放在标签右侧
            self.entries[key] = entry  # 记录键名对应的输入框

    # --- 文件操作
    def pick_and_load(self) -> None:
        chosen = filedialog.askopenfilename(  # 弹出“打开文件”对话框
            title="选择 Meta 文件", filetypes=[("Meta 文件", "*.meta"), ("所有文件", "*.*")])
        if chosen:  # 用户选了文件才继续
            self.load(Path(chosen))  # 载入该文件

    def load(self, path: Path) -> None:
        try:
            meta = read_meta(path)  # 尝试解析
        except (OSError, MetaFormatError) as exc:  # 解析失败弹错误框
            messagebox.showerror("解析失败", str(exc))
            return
        if not meta.dem or not meta.dom:  # 缺少 DEM 或 DOM 视为不合法
            messagebox.showerror("解析失败", "文件中缺少 DEM 或 DOM 分辨率记录")
            return
        self.meta = meta  # 保存解析结果
        self.source_path = path  # 记录来源路径
        self.path_var.set(str(path))  # 更新顶部路径显示
        self._fill(meta)  # 把字段填进输入框
        # 与 C++ 一致：解析的同时把每个字段追加写入同名 txt
        log_path = path.with_suffix(".txt")  # 同名但后缀改为 .txt
        try:
            write_log(log_path, meta)  # 写入日志
        except OSError as exc:  # 写日志失败也提示
            print(f"写日志失败：{exc}", file=sys.stderr)
            self.path_var.set(f"{path}（日志写入失败：{exc}）")
            return
        self.path_var.set(f"{path}    →  日志：{log_path}")  # 提示日志写到了哪

    def _put(self, key: str, value) -> None:
        entry = self.entries[key]  # 取出对应输入框
        entry.delete(0, tk.END)  # 清空原有内容
        entry.insert(0, str(value))  # 写入新值（转为字符串）

    def _fill(self, meta: MetaData) -> None:
        for index, value in enumerate(meta.bbox):  # 填 BBox 四值
            self._put(f"bbox{index}", f"{value:g}")
        for index, value in enumerate(meta.origin):  # 填原点两值
            self._put(f"origin{index}", f"{value:g}")
        self._put("xcount", meta.x_count)  # 填 X 边数
        self._put("ycount", meta.y_count)  # 填 Y 边数
        for prefix, item in (("dem", meta.dem[0]), ("dom", meta.dom[0])):  # 填首条 DEM/DOM
            self._put(f"{prefix}_res", f"{item.res:g}")  # 分辨率
            self._put(f"{prefix}_lyr", item.layer)  # 目标层
            for index, value in enumerate(item.bbox):  # 四至范围
                self._put(f"{prefix}_b{index}", f"{value:g}")
            for index, value in enumerate(item.counts):  # 列/行
                self._put(f"{prefix}_c{index}", value)

    def _collect(self) -> MetaData:
        if self.meta is None:  # 还没载入文件就报错
            raise ValueError("请先解析一个 Meta 文件")
        result = copy.deepcopy(self.meta)  # 深拷贝，避免直接改原始数据
        result.bbox = [self._num(f"bbox{i}") for i in range(4)]  # 从输入框读回 BBox
        result.origin = [self._num(f"origin{i}") for i in range(2)]  # 读回原点
        result.x_count = int(self._num("xcount"))  # 读回 X 边数
        result.y_count = int(self._num("ycount"))  # 读回 Y 边数
        for prefix, item in (("dem", result.dem[0]), ("dom", result.dom[0])):  # 读回分辨率字段
            item.res = float(self._num(f"{prefix}_res"))  # 分辨率
            item.layer = int(self._num(f"{prefix}_lyr"))  # 目标层
            item.bbox = [float(self._num(f"{prefix}_b{i}")) for i in range(4)]  # 四至
            item.counts = [int(self._num(f"{prefix}_c{i}")) for i in range(2)]  # 列/行
        return result  # 返回修改后的数据

    def _num(self, key: str) -> float:
        text = self.entries[key].get().strip()  # 取输入框文本并去首尾空格
        if not text:  # 空值报错
            raise ValueError(f"字段 {key} 不能为空")
        try:
            return float(text)  # 尝试转成浮点数
        except ValueError as exc:  # 转换失败给出更明确的提示
            raise ValueError(f"字段 {key} 的数值无法识别：{text}") from exc

    def save_meta(self) -> None:
        try:
            meta = self._collect()  # 收集界面输入
        except ValueError as exc:  # 输入有误弹窗提示
            messagebox.showerror("输入有误", str(exc))
            return
        default = "HZ2.meta"  # 默认输出文件名
        if self.source_path:  # 若已载入文件，则默认输出到同目录 HZ2.meta
            default = self.source_path.with_name("HZ2.meta").name
        chosen = filedialog.asksaveasfilename(  # 弹出“另存为”对话框
            title="生成 Meta 文件", initialfile=default, defaultextension=".meta",
            filetypes=[("Meta 文件", "*.meta"), ("所有文件", "*.*")])
        if not chosen:  # 用户取消则不做任何事
            return
        try:
            write_meta(Path(chosen), meta)  # 写回新文件
        except OSError as exc:  # 写文件失败弹窗
            messagebox.showerror("生成失败", str(exc))
            return
        messagebox.showinfo("生成完成", f"已生成：\n{chosen}")  # 成功提示


# --------------------------------------------------------------------- 入口 --

def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # 让标准输出支持 UTF-8，避免中文乱码
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="EditMeta 二进制读写（Python 复刻版）")  # 命令行解析器
    parser.add_argument("meta", nargs="?", type=Path, help="要解析的 .meta 文件")  # 位置参数：文件路径
    parser.add_argument("--dump", action="store_true", help="命令行打印解析结果后退出")  # 开关：仅打印
    parser.add_argument("-o", "--output", type=Path, help="把解析结果原样写出到指定文件后退出")  # 输出文件
    parser.add_argument("--log", type=Path, help="解析时把逐字段日志追加写入该 txt")  # 日志文件
    args = parser.parse_args(argv)  # 解析参数

    if args.meta is None:  # 没传文件就直接开界面
        EditMetaApp().mainloop()
        return 0

    try:
        meta = read_meta(args.meta)  # 解析传入的文件
    except (OSError, MetaFormatError) as exc:  # 失败打印到标准错误并退出码 1
        print(f"解析失败：{exc}", file=sys.stderr)
        return 1

    if args.log:  # 若要求写日志
        write_log(args.log, meta)
        print(f"日志已写入：{args.log}")
    if args.output:  # 若要求原样写出
        write_meta(args.output, meta)
        print(f"已生成：{args.output}")
    if args.dump or args.log or args.output:  # 命令行模式下打印解析结果
        print(dump_text(meta))
        return 0
    EditMetaApp(args.meta).mainloop()  # 否则用界面打开该文件
    return 0


if __name__ == "__main__":  # 仅当直接运行本文件时才执行
    raise SystemExit(main())  # 调用 main 并以它的返回值作为进程退出码

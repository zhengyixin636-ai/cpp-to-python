#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C++ → Python 转换结果校验脚本。

功能：
1. 检查生成的 Python 文件语法是否可解析；
2. 扫描是否残留 C++ 语法特征（#include、std::、new/delete、cout 等）；
3. 汇总 TODO(CPP2PY-*) / NOTE(CPP2PY-NOTE) 标注；
4. 可选调用外部测试命令做行为验证。

用法：
    python validate_conversion.py output.py
    python validate_conversion.py output.py --json
    python validate_conversion.py output.py --tests-cmd "python -m pytest tests -q"

退出码：
    0  通过（无语法错误、无 C++ 残留、无 BLOCKER 标注）
    1  存在语法错误或 C++ 语法残留，必须修复
    2  无阻断问题，但存在 TODO(CPP2PY-BLOCKER)，需人工确认
"""

from __future__ import annotations  # 允许在注解里使用较新的类型写法

import argparse  # 导入 argparse，用于解析命令行参数
import ast  # 导入 ast，用于把源码解析为抽象语法树
import io  # 导入 io，用于把字符串包装成可读的文件对象
import json  # 导入 json，用于输出 JSON 格式报告
import re  # 导入 re，用于正则匹配 C++ 残留特征
import subprocess  # 导入 subprocess，用于执行外部测试命令
import sys  # 导入 sys，用于向标准错误输出与设置退出码
import tokenize  # 导入 tokenize，用于在扫描前剔除注释与字符串
from pathlib import Path  # 导入 Path，用于跨平台处理文件路径

# 严重级规则：命中即判定为「必须修复」的 C++ 残留，每项为 (规则名, 正则, 说明)
ERROR_RULES: list[tuple[str, str, str]] = [
    ("cpp-include", r"^[ \t]*#[ \t]*include\b", "C++ 预处理指令 #include，应改为 import"),
    ("cpp-preproc", r"^[ \t]*#[ \t]*(define|undef|pragma|ifndef|ifdef|endif|elif)\b", "C++ 预处理指令，应改为常量、函数或配置分支"),
    ("cpp-std-scope", r"\bstd[ \t]*::", "std:: 命名空间限定，应改为对应的 Python 能力"),
    ("cpp-nullptr", r"\bnullptr\b", "nullptr 应改为 None"),
    ("cpp-new", r"\bnew[ \t]+[A-Za-z_]\w*", "new 表达式应删除，改为直接构造对象"),
    ("cpp-delete", r"\bdelete[ \t]*(\[[ \t]*\])?[ \t]*[A-Za-z_\[]", "delete 应删除，Python 自动管理内存"),
    ("cpp-c-memory", r"\b(malloc|calloc|realloc|sizeof|memcpy|memmove|memset)[ \t]*\(", "C 内存函数应改为 Python 容器或 struct 模块"),
    ("cpp-iostream", r"\b(cout|cin|cerr|clog|endl)\b", "iostream 对象应改为 print() / input()"),
    ("cpp-template", r"\btemplate[ \t]*<", "模板语法应改为鸭子类型或 typing.Generic"),
    ("cpp-using-namespace", r"\busing[ \t]+namespace\b", "using namespace 应删除"),
    ("cpp-typedef", r"\btypedef\b", "typedef 应改为类型别名或直接删除"),
    ("cpp-throw-catch", r"\b(throw|catch)[ \t]", "throw / catch 应改为 raise / try-except"),
]

# 可疑级规则：可能是残留也可能是误报，需人工确认，每项为 (规则名, 正则, 说明)
WARN_RULES: list[tuple[str, str, str]] = [
    ("cpp-scope-resolve", r"(?<![\w\[\d])[A-Za-z_]\w*[ \t]*::[ \t]*\w+", ":: 作用域解析，Python 用 . 或模块导入"),
    ("cpp-type-decl", r"\b(int|long|short|unsigned|signed|float|double|char|bool|void|auto|size_t|u?int\d+_t)[ \t]+[A-Za-z_]\w*[ \t]*(=[^=;]|[;,)])", "疑似 C++ 类型声明，请人工确认"),
    ("cpp-arrow-member", r"[A-Za-z_]\w*[ \t]*->[ \t]*", "-> 成员访问，Python 用 ."),
    ("cpp-literal", r"\b(NULL|TRUE|FALSE|true|false)\b", "C++ 字面量，应改为 None / True / False"),
    ("cpp-access-specifier", r"^[ \t]*(public|private|protected)[ \t]*:", "C++ 访问说明符，Python 靠命名约定"),
    ("cpp-keyword", r"\b(virtual|constexpr|inline|friend|explicit|mutable|volatile|register)\b", "C++ 关键字残留"),
    ("cpp-struct-enum-ns", r"\b(struct[ \t]+\w+|enum[ \t]+(class|struct)?[ \t]*\w+|namespace[ \t]+\w+)", "struct / enum / namespace 应改为 dataclass / Enum / 模块"),
    ("cpp-c-func", r"\b(printf|scanf|sprintf|atoi|atof|strlen|strcpy)[ \t]*\(", "C 风格函数应改为 f-string / int() / float() / len()"),
    ("cpp-trailing-semicolon", r";[ \t]*$", "行尾分号在 Python 中没有意义"),
]

# 用于识别「看起来像 Python 注释、实际是 C++ 预处理指令」的行，避免被误抹掉
PREPROC_COMMENT = re.compile(r"^#\s*(include|define|undef|pragma|ifndef|ifdef|endif|elif|if|else|error)\b")

# 用于匹配转换标注：# TODO(CPP2PY-BLOCKER): 说明  或  # NOTE(CPP2PY-NOTE): 说明（兼容不带后缀的写法）
MARKER_PATTERN = re.compile(r"#\s*(TODO|NOTE)\s*\(\s*CPP2PY(?:-([A-Za-z]+))?\s*\)\s*:?\s*(.*)")

# 用于查找未带标注的占位实现
PLACEHOLDER_PATTERN = re.compile(r"\braise\s+NotImplementedError\b")


def blank_token(buf: list[list[str]], start: tuple[int, int], end: tuple[int, int]) -> None:
    """把指定词法区间内的字符替换为空格（保留换行，以维持行号）。"""
    s_row, s_col = start  # 取出起始行号与列号（行号从 1 开始，列号从 0 开始）
    e_row, e_col = end  # 取出结束行号与列号
    for row in range(s_row, e_row + 1):  # 逐行处理该区间覆盖的所有行
        if row - 1 >= len(buf):  # 若行号超出缓冲区范围则跳过，避免越界
            break  # 跳出当前循环
        line = buf[row - 1]  # 取出该行对应的字符列表
        col_from = s_col if row == s_row else 0  # 起始行从起始列开始，其余行从 0 开始
        col_to = e_col if row == e_row else len(line)  # 结束行到结束列为止，其余行到行尾
        for i in range(col_from, min(col_to, len(line))):  # 遍历需要替换的列范围
            if line[i] not in "\r\n":  # 换行符必须保留，否则行号会错乱
                line[i] = " "  # 把非换行字符替换为空格


def strip_comments_and_strings(source: str) -> str:
    """返回一个把注释与字符串内容抹成空格的副本，用于降低残留扫描的误报。"""
    buf = [list(line) for line in source.splitlines(keepends=True)]  # 按行拆成字符列表，保留行尾换行符
    try:  # 词法分析可能因源码本身不合法而失败，需要容错
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))  # 对源码做词法分析，得到全部 token
    except (tokenize.TokenError, IndentationError, SyntaxError):  # 捕获词法或缩进异常
        return source  # 无法分析时退回原文，交给语法检查环节报错
    for tok in tokens:  # 遍历每一个 token
        if tok.type == tokenize.COMMENT and PREPROC_COMMENT.match(tok.string):  # 形如 #include 的预处理指令不是普通注释
            continue  # 保留原样，以便被残留规则检出
        if tok.type == tokenize.COMMENT:  # 注释内容不参与残留扫描
            blank_token(buf, tok.start, tok.end)  # 把注释区间抹成空格
        elif tok.type == tokenize.STRING:  # 字符串内容不参与残留扫描（避免文档字符串误报）
            blank_token(buf, tok.start, tok.end)  # 把字符串区间抹成空格
    return "".join("".join(line) for line in buf)  # 把字符列表重新拼成完整字符串


def check_syntax(path: Path, source: str) -> dict:
    """用 compile 检查源码语法是否可解析，返回包含结果与错误信息的字典。"""
    result = {"ok": True, "error": None}  # 默认认为语法通过，错误信息为空
    try:  # 尝试编译源码；只编译不执行，因此是安全的
        compile(source, str(path), "exec")  # 用 exec 模式编译，等价于对整个模块做语法检查
    except SyntaxError as exc:  # 捕获语法错误
        result["ok"] = False  # 标记语法检查未通过
        result["error"] = {  # 组装错误详情，便于定位
            "line": exc.lineno,  # 出错的行号
            "column": exc.offset,  # 出错的列号
            "message": exc.msg,  # 错误描述
            "text": (exc.text or "").rstrip("\n"),  # 出错行的源码文本
        }
    return result  # 返回语法检查结果


def scan_residue(code_only: str) -> list[dict]:
    """在已剔除注释与字符串的源码上扫描 C++ 残留特征，返回问题列表。"""
    issues: list[dict] = []  # 用于收集所有扫描到的问题
    lines = code_only.splitlines()  # 把源码按行拆分，便于展示出错行内容
    for level, rules in (("error", ERROR_RULES), ("warn", WARN_RULES)):  # 先扫严重级，再扫可疑级
        for name, pattern, message in rules:  # 逐条规则检查
            regex = re.compile(pattern, re.MULTILINE)  # 编译正则，启用多行模式以支持 ^ 匹配行首
            for match in regex.finditer(code_only):  # 在源码中查找所有匹配位置
                line_no = code_only.count("\n", 0, match.start()) + 1  # 由字符偏移量换算出行号
                snippet = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ""  # 取出该行内容用于展示
                issues.append({  # 把问题加入结果列表
                    "level": level,  # 问题级别：error 或 warn
                    "rule": name,  # 命中的规则名
                    "line": line_no,  # 问题所在行号
                    "message": message,  # 规则对应的说明文案
                    "snippet": snippet,  # 该行源码片段
                })
    issues.sort(key=lambda item: (item["level"] != "error", item["line"]))  # 严重级排前，同级按行号排序
    return issues  # 返回扫描结果


def scan_markers(source: str) -> list[dict]:
    """扫描全部 CPP2PY 标注，返回标注列表。"""
    markers: list[dict] = []  # 用于收集所有标注
    for line_no, line in enumerate(source.splitlines(), start=1):  # 逐行遍历原始源码
        match = MARKER_PATTERN.search(line)  # 在本行查找标注格式
        if match:  # 若找到标注
            markers.append({  # 记录标注详情
                "line": line_no,  # 标注所在行号
                "kind": match.group(1).upper(),  # 标注种类：TODO 或 NOTE
                "level": (match.group(2) or "NOTE").upper(),  # 标注级别：BLOCKER / REVIEW / NOTE（无后缀时归为 NOTE）
                "text": match.group(3).strip(),  # 标注的说明文字
            })
    return markers  # 返回标注列表


def scan_unannotated_placeholders(source: str) -> list[dict]:
    """查找 raise NotImplementedError 但附近没有 CPP2PY 标注的位置。"""
    problems: list[dict] = []  # 用于收集未标注的占位实现
    lines = source.splitlines()  # 把源码按行拆分
    for index, line in enumerate(lines):  # 逐行检查
        if not PLACEHOLDER_PATTERN.search(line):  # 若本行没有 NotImplementedError 则跳过
            continue  # 继续检查下一行
        start = max(0, index - 3)  # 向前回溯最多 3 行，寻找是否有标注
        nearby = "\n".join(lines[start:index + 1])  # 拼接附近几行文本
        if "CPP2PY" not in nearby:  # 附近没有 CPP2PY 标注，说明是静默占位
            problems.append({  # 记录该问题
                "line": index + 1,  # 问题所在行号（转换为从 1 开始）
                "message": "存在未标注的占位实现，应补 TODO(CPP2PY-BLOCKER) 说明或改为真实实现",
                "snippet": line.strip(),  # 该行源码片段
            })
    return problems  # 返回问题列表


def collect_stats(source: str) -> dict:
    """统计模块中的类数量、函数数量与是否存在 __main__ 入口。"""
    stats = {"classes": 0, "functions": 0, "has_main_guard": False}  # 初始化统计结果
    try:  # 解析源码为抽象语法树
        tree = ast.parse(source)  # 把源码解析成 AST
    except SyntaxError:  # 语法错误时无法统计，返回默认值
        return stats  # 返回未填充的统计结果
    for node in ast.walk(tree):  # 遍历 AST 中的所有节点
        if isinstance(node, ast.ClassDef):  # 节点是类定义
            stats["classes"] += 1  # 类计数加一
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):  # 节点是函数或异步函数定义
            stats["functions"] += 1  # 函数计数加一
    stats["has_main_guard"] = '__name__ == "__main__"' in source or "__name__ == '__main__'" in source  # 判断是否含主入口
    return stats  # 返回统计结果


def run_tests(command: str) -> dict:
    """执行外部测试命令，返回是否成功与输出尾部内容。"""
    result = {"ok": True, "command": command, "output": ""}  # 默认认为测试通过
    completed = subprocess.run(command, shell=True, capture_output=True, text=True)  # 执行测试命令并捕获输出
    result["ok"] = completed.returncode == 0  # 依据返回码判断测试是否通过
    tail = (completed.stdout + completed.stderr).strip().splitlines()  # 合并标准输出与错误输出并分行
    result["output"] = "\n".join(tail[-20:])  # 只保留最后 20 行，避免报告过长
    return result  # 返回测试结果


def build_report(path: Path, tests_cmd: str | None) -> dict:
    """对单个文件执行全部检查，汇总为一份结构化报告。"""
    source = path.read_text(encoding="utf-8")  # 以 UTF-8 读取源文件内容
    report: dict = {"file": str(path)}  # 初始化报告，先记录文件名
    report["syntax"] = check_syntax(path, source)  # 执行语法检查
    code_only = strip_comments_and_strings(source)  # 剔除注释与字符串，得到用于扫描的纯净代码
    report["residue"] = scan_residue(code_only)  # 扫描 C++ 残留特征
    report["markers"] = scan_markers(source)  # 扫描所有 CPP2PY 标注
    report["placeholders"] = scan_unannotated_placeholders(source)  # 检查未标注的占位实现
    report["stats"] = collect_stats(source)  # 统计类与函数数量
    if tests_cmd:  # 若用户提供了测试命令
        report["tests"] = run_tests(tests_cmd)  # 执行测试并记录结果
    else:  # 未提供测试命令时
        report["tests"] = None  # 标记为未执行测试
    return report  # 返回汇总报告


def summarize(report: dict) -> tuple[int, str]:
    """根据报告计算退出码与一句话结论。"""
    syntax_ok = report["syntax"]["ok"]  # 取出语法检查是否通过
    error_count = sum(1 for item in report["residue"] if item["level"] == "error")  # 统计严重级残留数量
    blocker = [m for m in report["markers"] if m["level"] == "BLOCKER"]  # 筛出所有 BLOCKER 标注
    placeholder_count = len(report["placeholders"])  # 未标注占位实现的数量
    tests = report.get("tests")  # 取出测试结果（可能为 None）

    if not syntax_ok or error_count > 0 or placeholder_count > 0:  # 语法错误、严重残留或静默占位
        return 1, "未通过：存在语法错误或 C++ 残留，必须修复后再交付"  # 返回退出码 1 与结论
    if tests is not None and not tests["ok"]:  # 测试命令执行但失败
        return 1, "未通过：转换结果未通过行为测试"  # 返回退出码 1 与结论
    if blocker:  # 存在需人工确认的 BLOCKER
        return 2, f"有条件通过：存在 {len(blocker)} 处 TODO(CPP2PY-BLOCKER)，需人工确认"  # 返回退出码 2 与结论
    return 0, "通过：无语法错误、无 C++ 残留、无阻断标注"  # 返回退出码 0 与结论


def print_report(report: dict, exit_code: int, conclusion: str) -> None:
    """把报告以可读文本形式打印到标准输出。"""
    print("=" * 60)  # 打印分隔线，作为报告开头
    print("C++ → Python 转换校验报告")  # 打印报告标题
    print("=" * 60)  # 打印分隔线
    print(f"文件：{report['file']}")  # 打印被检查的文件路径

    syntax = report["syntax"]  # 取出语法检查结果
    if syntax["ok"]:  # 语法检查通过
        print("[语法] 通过")  # 输出语法通过
    else:  # 语法检查失败
        err = syntax["error"]  # 取出错误详情
        print(f"[语法] 失败：第 {err['line']} 行 第 {err['column']} 列 —— {err['message']}")  # 输出错误位置与原因
        print(f"        {err['text']}")  # 输出出错行的源码

    residue = report["residue"]  # 取出残留扫描结果
    errors = [i for i in residue if i["level"] == "error"]  # 筛选严重级问题
    warns = [i for i in residue if i["level"] == "warn"]  # 筛选可疑级问题
    print(f"[残留] 严重 {len(errors)} 项，可疑 {len(warns)} 项")  # 输出残留统计
    for item in errors:  # 逐条输出严重级问题
        print(f"    ERROR  行 {item['line']:>4}  [{item['rule']}] {item['message']}")  # 输出问题行号与说明
        print(f"           | {item['snippet']}")  # 输出对应源码片段
    for item in warns:  # 逐条输出可疑级问题
        print(f"    WARN   行 {item['line']:>4}  [{item['rule']}] {item['message']}")  # 输出问题行号与说明
        print(f"           | {item['snippet']}")  # 输出对应源码片段

    markers = report["markers"]  # 取出标注列表
    counts: dict[str, int] = {}  # 用于按级别统计标注数量
    for marker in markers:  # 遍历每条标注
        counts[marker["level"]] = counts.get(marker["level"], 0) + 1  # 对应级别计数加一
    print(f"[标注] " + "，".join(f"{k} x{v}" for k, v in counts.items()) if counts else "[标注] 无")  # 输出标注统计
    for marker in markers:  # 逐条输出标注详情
        print(f"    行 {marker['line']:>4}  {marker['kind']}(CPP2PY-{marker['level']}): {marker['text']}")  # 输出标注内容

    for item in report["placeholders"]:  # 逐条输出未标注的占位实现
        print(f"    ERROR  行 {item['line']:>4}  {item['message']}")  # 输出问题行号与说明
        print(f"           | {item['snippet']}")  # 输出对应源码片段

    stats = report["stats"]  # 取出统计结果
    print(f"[统计] 类 {stats['classes']} 个，函数 {stats['functions']} 个，主入口 {'有' if stats['has_main_guard'] else '无'}")  # 输出统计信息

    tests = report.get("tests")  # 取出测试结果
    if tests is None:  # 未提供测试命令
        print("[测试] 未执行（可用 --tests-cmd 指定测试命令）")  # 提示未执行测试
    else:  # 已执行测试
        print(f"[测试] {'通过' if tests['ok'] else '失败'}：{tests['command']}")  # 输出测试命令与结果
        if tests["output"]:  # 若有测试输出
            print(tests["output"])  # 打印测试输出尾部内容

    print("-" * 60)  # 打印分隔线
    print(f"结论：{conclusion}（退出码 {exit_code}）")  # 输出最终结论与退出码


def main() -> int:
    """程序入口：解析参数、执行校验、输出结果并返回退出码。"""
    parser = argparse.ArgumentParser(description="校验 C++ → Python 转换结果")  # 创建参数解析器
    parser.add_argument("files", nargs="+", help="待校验的 Python 文件路径")  # 位置参数：一个或多个文件路径
    parser.add_argument("--tests-cmd", dest="tests_cmd", default=None, help="可选的测试命令，例如 \"python -m pytest tests -q\"")  # 可选参数：测试命令
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出报告")  # 可选参数：是否输出 JSON
    args = parser.parse_args()  # 解析命令行参数

    worst_code = 0  # 记录所有文件中最严重的退出码
    reports = []  # 收集每个文件的报告，便于 JSON 输出
    for name in args.files:  # 逐个处理待校验文件
        path = Path(name)  # 把路径字符串转为 Path 对象
        if not path.exists():  # 文件不存在
            print(f"[错误] 文件不存在：{path}", file=sys.stderr)  # 向标准错误输出提示
            worst_code = max(worst_code, 1)  # 更新最严重退出码
            continue  # 跳过该文件，继续处理下一个
        report = build_report(path, args.tests_cmd)  # 对该文件执行全部检查
        code, conclusion = summarize(report)  # 计算该文件结论与退出码
        report["exit_code"] = code  # 把退出码写入报告
        report["conclusion"] = conclusion  # 把结论写入报告
        reports.append(report)  # 收集报告
        worst_code = max(worst_code, code)  # 更新最严重退出码
        if not args.json:  # 非 JSON 模式
            print_report(report, code, conclusion)  # 以文本形式打印报告
            print()  # 打印空行，分隔多个文件的报告

    if args.json:  # JSON 模式
        payload = reports if len(reports) > 1 else (reports[0] if reports else {})  # 单文件输出对象，多文件输出数组
        print(json.dumps(payload, ensure_ascii=False, indent=2))  # 输出 JSON，保留中文
    return worst_code  # 返回最严重退出码


if __name__ == "__main__":  # 仅当直接运行本脚本时执行
    sys.exit(main())  # 以 main 的返回值作为进程退出码

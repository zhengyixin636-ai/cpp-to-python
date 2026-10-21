# -*- coding: utf-8 -*-
"""针对 `scripts/validate_conversion.py` 的单元测试。"""  # 模块说明：测试 C++→Python 转换校验脚本

import importlib.util  # 导入 importlib.util，用于按文件路径动态加载模块
import io  # 导入 io，用于构造临时文件对象
import json  # 导入 json，用于校验 --json 输出
import sys  # 导入 sys，用于操控 argv 与捕获退出码
from pathlib import Path  # 导入 Path，用于拼出被测试脚本的绝对路径
from types import SimpleNamespace  # 导入 SimpleNamespace，用于伪造 subprocess 返回对象

import pytest  # 导入 pytest，作为测试框架

# 计算出被测试脚本的绝对路径（tests 目录的上一级的 scripts 目录）
SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "validate_conversion.py"

# 动态加载脚本为模块，避免把它当成顶层包导入导致命名冲突
_SPEC = importlib.util.spec_from_file_location("validate_conversion", SCRIPT_PATH)
vc = importlib.util.module_from_spec(_SPEC)  # 按 spec 创建一个空模块对象
_SPEC.loader.exec_module(vc)  # 执行脚本源码，使其中的函数/常量可用


def _write_tmp(tmp_path: Path, name: str, content: str) -> Path:
    """把一段源码写入临时目录，返回文件路径。"""
    p = tmp_path / name  # 拼出完整临时文件路径
    p.write_text(content, encoding="utf-8")  # 以 UTF-8 写入内容
    return p  # 返回该路径，供被测函数读取


# ---------- blank_token / strip_comments_and_strings ----------

def test_strip_removes_string_literal_residue():
    """字符串字面量里的 std:: 不应被当成 C++ 残留。"""
    src = 'x = "use std::vector here"\n'  # 内容里有 std::，但位于字符串内
    out = vc.strip_comments_and_strings(src)  # 抹除字符串与注释后的副本
    assert "std::" not in out  # 字符串被清空，残留扫描应找不到


def test_strip_keeps_preproc_comment():
    """形如 #include 的注释必须保留，以便被残留规则检出。"""
    src = "#include <vector>  # 这是注释\n"  # 行首是预处理指令式注释
    out = vc.strip_comments_and_strings(src)  # 抹除普通注释后
    assert "#include" in out  # 预处理式注释应保留


def test_strip_removes_normal_comment():
    """普通注释里的 std:: 不应被当成残留。"""
    src = "# 这里提到 std::map\n"  # 普通注释
    out = vc.strip_comments_and_strings(src)  # 抹除后
    assert "std::" not in out  # 注释被清空


# ---------- check_syntax ----------

def test_check_syntax_ok():
    """语法正确的源码应判定通过。"""
    r = vc.check_syntax(Path("a.py"), "x = 1\n")  # 检查一段合法源码
    assert r["ok"] is True  # ok 应为 True
    assert r["error"] is None  # 错误信息应为空


def test_check_syntax_error():
    """语法错误的源码应返回错误位置。"""
    r = vc.check_syntax(Path("a.py"), "x = \n")  # 非法赋值语句
    assert r["ok"] is False  # ok 应为 False
    assert r["error"]["line"] == 1  # 错误在第 1 行


# ---------- scan_residue ----------

def test_scan_residue_error_rules():
    """严重级 C++ 残留应被检出并标记 level=error。"""
    src = "#include <vector>\nint* p = new Foo();\ncout << x;\n"  # 含 include/new/cout
    issues = vc.scan_residue(vc.strip_comments_and_strings(src))  # 扫描残留
    errors = [i for i in issues if i["level"] == "error"]  # 筛选严重级
    rules = {i["rule"] for i in errors}  # 取出命中的规则名集合
    assert "cpp-include" in rules  # 应包含 include 规则
    assert "cpp-new" in rules  # 应包含 new 规则
    assert "cpp-iostream" in rules  # 应包含 iostream 规则


def test_scan_residue_warn_rules():
    """可疑级残留（如 true 字面量、->）应被标记 level=warn。"""
    src = "flag = true\nobj->method()\n"  # 含 C++ 字面量与箭头
    issues = vc.scan_residue(vc.strip_comments_and_strings(src))  # 扫描
    warns = [i for i in issues if i["level"] == "warn"]  # 筛选可疑级
    rules = {i["rule"] for i in warns}  # 规则名集合
    assert "cpp-literal" in rules  # 应检出 true 字面量
    assert "cpp-arrow-member" in rules  # 应检出 -> 成员访问


def test_scan_residue_line_number():
    """残留应正确换算出行号（前面有空行）。"""
    src = "\n\nnullptr\n"  # 第 3 行才是 nullptr
    issues = vc.scan_residue(vc.strip_comments_and_strings(src))  # 扫描
    assert any(i["line"] == 3 for i in issues)  # 命中行号应为 3


# ---------- scan_markers ----------

def test_scan_markers_all_kinds():
    """BLOCKER / REVIEW / NOTE（含新写法）都应被正确识别。"""
    src = (
        "# TODO(CPP2PY-BLOCKER): 原因\n"  # 阻断标注
        "# TODO(CPP2PY-REVIEW): 风险\n"  # 复核标注
        "# NOTE(CPP2PY-NOTE): 说明\n"  # 新写法 NOTE
        "# NOTE(CPP2PY): 旧写法\n"  # 旧写法 NOTE（脚本已兼容）
    )
    markers = vc.scan_markers(src)  # 扫描全部标注
    levels = {m["level"] for m in markers}  # 取出 level 集合
    assert "BLOCKER" in levels  # 应识别 BLOCKER
    assert "REVIEW" in levels  # 应识别 REVIEW
    assert "NOTE" in levels  # 应识别 NOTE（两种写法都归类为 NOTE）
    assert len(markers) == 4  # 共 4 条标注


def test_scan_markers_ignores_plain_comment():
    """普通注释不应被误判为标注。"""
    src = "# 这只是普通说明\n"  # 没有 CPP2PY 关键字
    assert vc.scan_markers(src) == []  # 结果应为空列表


# ---------- scan_unannotated_placeholders ----------

def test_placeholder_detected_without_marker():
    """附近没有 CPP2PY 标注的 NotImplementedError 应被记为问题。"""
    src = "def f():\n    raise NotImplementedError\n"  # 裸占位
    problems = vc.scan_unannotated_placeholders(src)  # 扫描占位
    assert len(problems) == 1  # 应检出 1 处


def test_placeholder_ok_with_marker():
    """3 行内有 CPP2PY 标注时不应记为问题。"""
    src = (
        "# TODO(CPP2PY-BLOCKER): 需人工实现\n"  # 标注
        "def f():\n"  # 函数定义
        "    raise NotImplementedError\n"  # 带标注的占位
    )
    problems = vc.scan_unannotated_placeholders(src)  # 扫描
    assert problems == []  # 不应报错


# ---------- collect_stats ----------

def test_collect_stats_counts():
    """应能统计类、函数数量与主入口。"""
    src = (
        "class A:\n"  # 一个类
        "    def m(self):\n"  # 一个方法
        "        pass\n"
        "def g():\n"  # 一个顶层函数
        "    pass\n"
        "if __name__ == '__main__':\n"  # 主入口
        "    pass\n"
    )
    stats = vc.collect_stats(src)  # 统计
    assert stats["classes"] == 1  # 类数量为 1
    assert stats["functions"] == 2  # 函数（含方法）共 2
    assert stats["has_main_guard"] is True  # 检测到主入口


def test_collect_stats_invalid_source():
    """语法错误时统计应安全返回默认值。"""
    stats = vc.collect_stats("def (:")  # 非法源码
    assert stats["classes"] == 0  # 类为 0
    assert stats["functions"] == 0  # 函数为 0


# ---------- summarize ----------

def _report(syntax_ok=True, errors=0, placeholders=0, blockers=0, tests_ok=None):
    """构造一个 summarize 需要的报告字典。"""
    return {
        "syntax": {"ok": syntax_ok},  # 语法是否通过
        "residue": [{"level": "error"} for _ in range(errors)],  # 严重残留列表
        "markers": [{"level": "BLOCKER", "line": 1, "kind": "TODO", "text": "x"} for _ in range(blockers)],  # BLOCKER 标注列表
        "placeholders": [{} for _ in range(placeholders)],  # 静默占位列表
        "tests": (None if tests_ok is None else {"ok": tests_ok}),  # 测试结果（或 None）
    }


def test_summarize_pass():
    """无问题时应返回退出码 0。"""
    code, _ = vc.summarize(_report())  # 干净报告
    assert code == 0  # 退出码 0


def test_summarize_blocker():
    """仅有 BLOCKER 标注应返回退出码 2。"""
    code, _ = vc.summarize(_report(blockers=1))  # 含 1 个 BLOCKER
    assert code == 2  # 退出码 2


def test_summarize_syntax_error():
    """语法错误应返回退出码 1。"""
    code, _ = vc.summarize(_report(syntax_ok=False))  # 语法失败
    assert code == 1  # 退出码 1


def test_summarize_error_residue():
    """严重残留应返回退出码 1。"""
    code, _ = vc.summarize(_report(errors=1))  # 有 1 条严重残留
    assert code == 1  # 退出码 1


def test_summarize_placeholder():
    """静默占位应返回退出码 1。"""
    code, _ = vc.summarize(_report(placeholders=1))  # 有 1 个占位
    assert code == 1  # 退出码 1


def test_summarize_tests_fail():
    """测试命令失败应返回退出码 1。"""
    code, _ = vc.summarize(_report(tests_ok=False))  # 行为测试未通过
    assert code == 1  # 退出码 1


# ---------- run_tests ----------

def test_run_tests_ok(monkeypatch):
    """外部测试命令返回 0 时应判为通过。"""
    ns = SimpleNamespace(returncode=0, stdout="1 passed", stderr="")  # 伪造成功结果
    monkeypatch.setattr(vc.subprocess, "run", lambda *a, **k: ns)  # 替换 subprocess.run
    r = vc.run_tests("python -m pytest")  # 执行测试
    assert r["ok"] is True  # 应判为通过


def test_run_tests_fail(monkeypatch):
    """外部测试命令返回非 0 时应判为失败。"""
    ns = SimpleNamespace(returncode=1, stdout="", stderr="boom")  # 伪造失败结果
    monkeypatch.setattr(vc.subprocess, "run", lambda *a, **k: ns)  # 替换
    r = vc.run_tests("python -m pytest")  # 执行
    assert r["ok"] is False  # 应判为失败
    assert "boom" in r["output"]  # 输出尾部应包含错误信息


# ---------- build_report / print_report ----------

def test_build_report_clean(tmp_path):
    """对干净文件 build_report 不应抛异常，且统计正确。"""
    p = _write_tmp(tmp_path, "ok.py", "def f():\n    return 1\n")  # 干净文件
    rep = vc.build_report(p, None)  # 构建报告
    assert rep["syntax"]["ok"] is True  # 语法通过
    assert rep["residue"] == []  # 无残留
    assert rep["tests"] is None  # 未提供测试命令


def test_build_report_with_blocker(tmp_path):
    """含 BLOCKER 标注的文件应被统计到 markers 中。"""
    p = _write_tmp(tmp_path, "b.py", "# TODO(CPP2PY-BLOCKER): x\ndef f():\n    pass\n")  # 含标注
    rep = vc.build_report(p, None)  # 构建报告
    assert any(m["level"] == "BLOCKER" for m in rep["markers"])  # 应含 BLOCKER


def test_print_report_no_crash(capsys):
    """print_report 对任意报告应可正常打印，不崩溃。"""
    rep = _report(blockers=1)  # 构造一个含 BLOCKER 的报告
    rep["file"] = "dummy.py"  # 补上文件名
    rep["stats"] = {"classes": 0, "functions": 0, "has_main_guard": False}  # print_report 需要 stats
    rep["exit_code"] = 2  # 退出码
    rep["conclusion"] = "test"  # 结论
    vc.print_report(rep, 2, "test")  # 调用打印
    out = capsys.readouterr().out  # 捕获标准输出
    assert "结论" in out  # 输出应包含结论行


# ---------- main ----------

def test_main_pass(tmp_path, monkeypatch):
    """干净文件经 main 处理应返回退出码 0。"""
    p = _write_tmp(tmp_path, "ok.py", "x = 1\n")  # 干净文件
    monkeypatch.setattr(sys, "argv", ["validate_conversion.py", str(p)])  # 模拟命令行参数
    assert vc.main() == 0  # main 返回退出码 0


def test_main_error_residue(tmp_path, monkeypatch):
    """含 C++ 残留的文件应返回退出码 1。"""
    p = _write_tmp(tmp_path, "bad.py", "#include <vector>\n")  # 含 include 残留
    monkeypatch.setattr(sys, "argv", ["validate_conversion.py", str(p)])  # 模拟参数
    assert vc.main() == 1  # main 返回退出码 1


def test_main_blocker(tmp_path, monkeypatch):
    """仅含已标注 BLOCKER 的文件应返回退出码 2。"""
    p = _write_tmp(tmp_path, "b.py", "# TODO(CPP2PY-BLOCKER): x\nx = 1\n")  # 仅 BLOCKER
    monkeypatch.setattr(sys, "argv", ["validate_conversion.py", str(p)])  # 模拟参数
    assert vc.main() == 2  # main 返回退出码 2


def test_main_missing_file(tmp_path, monkeypatch):
    """不存在的文件应返回退出码 1（worst_code 取最大）。"""
    missing = tmp_path / "nope.py"  # 一个不存在的路径
    monkeypatch.setattr(sys, "argv", ["validate_conversion.py", str(missing)])  # 模拟参数
    assert vc.main() == 1  # main 返回退出码 1


def test_main_json_output(tmp_path, monkeypatch, capsys):
    """--json 模式应输出可解析的 JSON 且包含 exit_code。"""
    p = _write_tmp(tmp_path, "ok.py", "x = 1\n")  # 干净文件
    monkeypatch.setattr(sys, "argv", ["validate_conversion.py", str(p), "--json"])  # 带 --json
    vc.main()  # 调用入口
    out = capsys.readouterr().out  # 捕获输出
    payload = json.loads(out)  # 解析 JSON
    assert payload["exit_code"] == 0  # JSON 中应含退出码 0


def test_print_report_full_branches(capsys):
    """print_report 应覆盖 warn / 占位 / 测试通过 三条分支而不崩溃。"""
    rep = {  # 构造一个含各类信息的完整报告
        "file": "demo.py",  # 文件名
        "syntax": {"ok": True},  # 语法通过
        "residue": [  # 同时含 error 与 warn，便于渲染两种分支
            {"level": "error", "rule": "cpp-new", "message": "m1", "snippet": "new X", "line": 2},
            {"level": "warn", "rule": "cpp-literal", "message": "m2", "snippet": "true", "line": 3},
        ],
        "markers": [{"line": 4, "kind": "TODO", "level": "BLOCKER", "text": "x"}],  # 一条 BLOCKER
        "placeholders": [{"line": 5, "message": "占位", "snippet": "raise NotImplementedError"}],  # 一处占位
        "stats": {"classes": 1, "functions": 2, "has_main_guard": True},  # 统计信息
        "tests": {"ok": True, "command": "pytest", "output": "1 passed"},  # 测试通过
        "exit_code": 1,  # 退出码
        "conclusion": "c",  # 结论
    }
    vc.print_report(rep, 1, "c")  # 调用打印
    out = capsys.readouterr().out  # 捕获输出
    assert "[残留]" in out and "[测试]" in out and "1 passed" in out  # 各分支均已渲染


def test_main_multi_file(tmp_path, monkeypatch):
    """支持一次校验多个文件，退出码取最严重值。"""
    p1 = _write_tmp(tmp_path, "a.py", "x = 1\n")  # 干净文件 1
    p2 = _write_tmp(tmp_path, "b.py", "# TODO(CPP2PY-BLOCKER): y\nx=1\n")  # BLOCKER 文件 2
    monkeypatch.setattr(sys, "argv", ["validate_conversion.py", str(p1), str(p2)])  # 多文件参数
    assert vc.main() == 2  # 最严重退出码为 2


if __name__ == "__main__":  # 直接运行时也能跑测试
    sys.exit(pytest.main([__file__, "-v"]))  # 以详细模式执行 pytest

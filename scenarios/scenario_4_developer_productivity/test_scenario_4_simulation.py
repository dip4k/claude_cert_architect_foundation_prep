"""
Unit tests for Scenario 4: Developer Productivity with Claude simulation.
Runs 100% offline with zero token costs.
"""

import pytest
from scenarios.scenario_4_developer_productivity.simulation import DeveloperProductivityToolbox


def test_developer_toolbox_mcp_resource_read():
    toolbox = DeveloperProductivityToolbox({"a.py": "x=1"})
    res = toolbox.read_mcp_resource("resource://specs/openapi.json")
    assert res["success"] is True
    assert "Billing API" in res["name"]


def test_developer_toolbox_grep_and_glob():
    files = {
        "src/auth.py": "def login(): pass",
        "src/utils.py": "def helper(): pass",
        "tests/test_auth.py": "def test_login(): pass"
    }
    toolbox = DeveloperProductivityToolbox(files)
    glob_res = toolbox.glob_paths("tests/*.py")
    assert len(glob_res) == 1
    assert glob_res[0] == "tests/test_auth.py"

    grep_res = toolbox.grep_symbols("def login")
    assert len(grep_res) == 1
    assert grep_res[0]["file"] == "src/auth.py"


def test_developer_toolbox_edit_collision_and_fallback_recovery():
    files = {
        "calc.py": "def a(): return 1\ndef b(): return 1\n"
    }
    toolbox = DeveloperProductivityToolbox(files)

    # 1. Edit collision
    collision = toolbox.apply_edit("calc.py", "return 1", "return 2")
    assert collision["success"] is False
    assert collision["status"] == "AMBIGUOUS_COLLISION"

    # 2. Fallback recovery with expanded anchor
    recovery = toolbox.execute_edit_with_fallback(
        "calc.py",
        old_str="return 1",
        new_str="return 2",
        expanded_anchor="def a(): return 1"
    )
    assert recovery["final_status"] == "EXPANDED_ANCHOR_SUCCESS"
    assert "def a(): return 2" in toolbox.files["calc.py"]
    assert "def b(): return 1" in toolbox.files["calc.py"]


def test_developer_toolbox_fallback_to_read_write_when_no_anchor_provided():
    files = {
        "calc.py": "def a(): return 1\ndef b(): return 1\n"
    }
    toolbox = DeveloperProductivityToolbox(files)
    recovery = toolbox.execute_edit_with_fallback(
        "calc.py",
        old_str="return 1",
        new_str="return 99",
        expanded_anchor=None
    )
    assert recovery["final_status"] == "FALLBACK_READ_WRITE_SUCCESS"
    assert "return 99" in toolbox.files["calc.py"]


def test_developer_toolbox_file_not_found_error():
    toolbox = DeveloperProductivityToolbox({"a.py": "x=1"})
    res = toolbox.apply_edit("nonexistent.py", "x=1", "x=2")
    assert res["success"] is False
    assert res["status"] == "FILE_NOT_FOUND"


def test_developer_toolbox_read_and_write_tools():
    toolbox = DeveloperProductivityToolbox({"test.txt": "initial line"})
    read_res = toolbox.read_file("test.txt")
    assert read_res["success"] is True
    assert read_res["content"] == "initial line"

    write_res = toolbox.write_file("test.txt", "overwritten content")
    assert write_res["success"] is True
    assert write_res["status"] == "WRITTEN"
    assert toolbox.files["test.txt"] == "overwritten content"


def test_developer_toolbox_targeted_occurrence_and_full_replacement():
    files = {
        "calc.py": "def f1(): return 42\ndef f2(): return 42\n"
    }
    toolbox = DeveloperProductivityToolbox(files)

    # Fallback targeting occurrence 2 specifically
    rec = toolbox.execute_edit_with_fallback(
        "calc.py",
        old_str="return 42",
        new_str="return 100",
        expanded_anchor=None,
        target_occurrence=2
    )
    assert rec["final_status"] == "FALLBACK_READ_WRITE_SUCCESS"
    assert "def f1(): return 42" in toolbox.files["calc.py"]
    assert "def f2(): return 100" in toolbox.files["calc.py"]

    # Fallback with explicit full replacement content on ambiguous anchor
    toolbox.files["calc.py"] = "def f1(): return 50\ndef f2(): return 50\n"
    rec2 = toolbox.execute_edit_with_fallback(
        "calc.py",
        old_str="return 50",
        new_str="return 999",
        full_replacement_content="def f1(): return 1\ndef f2(): return 2\n"
    )
    assert rec2["final_status"] == "FALLBACK_READ_WRITE_SUCCESS"
    assert toolbox.files["calc.py"] == "def f1(): return 1\ndef f2(): return 2\n"



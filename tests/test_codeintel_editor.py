"""Test écriture contrôlée (SafeEditor) + Git (garde-fous, dry-run, backup, sandbox)."""

import subprocess

import pytest

from ai_engine.modules.codeintel.editor import GuardrailError, get_safe_editor
from ai_engine.modules.codeintel.git_tools import get_git_intelligence


def test_write_dry_run_then_confirm(tmp_path):
    ed = get_safe_editor()
    root = str(tmp_path)
    prev = ed.write(root, "a.py", "print('hi')\n", confirm=False)
    assert prev["dry_run"] is True and not (tmp_path / "a.py").exists()
    res = ed.write(root, "a.py", "print('hi')\n", confirm=True)
    assert res["written"] is True and (tmp_path / "a.py").read_text() == "print('hi')\n"


def test_overwrite_requires_flag_and_backups(tmp_path):
    ed = get_safe_editor()
    root = str(tmp_path)
    ed.write(root, "b.py", "v1\n", confirm=True)
    with pytest.raises(GuardrailError):
        ed.write(root, "b.py", "v2\n", confirm=True)  # pas d'allow_overwrite
    res = ed.write(root, "b.py", "v2\n", confirm=True, allow_overwrite=True)
    assert res["overwritten"] is True and res["backup_id"]
    # restauration de la v1
    ed.restore(res["backup_id"])
    assert (tmp_path / "b.py").read_text() == "v1\n"


def test_edit_unique_replace(tmp_path):
    ed = get_safe_editor()
    root = str(tmp_path)
    ed.write(root, "c.py", "x = 1\ny = 2\n", confirm=True)
    prev = ed.edit(root, "c.py", "y = 2", "y = 3", confirm=False)
    assert prev["dry_run"] is True and "y = 3" in prev["diff"]
    ed.edit(root, "c.py", "y = 2", "y = 3", confirm=True)
    assert (tmp_path / "c.py").read_text() == "x = 1\ny = 3\n"


def test_edit_non_unique_rejected(tmp_path):
    ed = get_safe_editor()
    root = str(tmp_path)
    ed.write(root, "d.py", "a\na\n", confirm=True)
    with pytest.raises(GuardrailError):
        ed.edit(root, "d.py", "a", "b", confirm=True)


def test_path_sandbox_blocks_traversal(tmp_path):
    ed = get_safe_editor()
    with pytest.raises(GuardrailError):
        ed.write(str(tmp_path), "../evil.py", "x", confirm=True)


def test_protected_zone_blocked(tmp_path):
    ed = get_safe_editor()
    with pytest.raises(GuardrailError):
        ed.write(str(tmp_path), ".git/config", "x", confirm=True)


def test_delete_soft_reversible(tmp_path):
    ed = get_safe_editor()
    root = str(tmp_path)
    ed.write(root, "e.py", "data\n", confirm=True)
    res = ed.delete(root, "e.py", confirm=True)
    assert res["deleted"] is True and not (tmp_path / "e.py").exists()
    ed.restore(res["backup_id"])
    assert (tmp_path / "e.py").read_text() == "data\n"


def test_git_status_non_repo(tmp_path):
    assert get_git_intelligence().status(str(tmp_path))["repo"] is False


def test_git_checkpoint_and_commit(tmp_path):
    git = get_git_intelligence()
    root = str(tmp_path)
    try:
        subprocess.run(["git", "init"], cwd=root, capture_output=True, timeout=20)
        subprocess.run(["git", "config", "user.email", "t@t.co"], cwd=root, capture_output=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=root, capture_output=True)
    except Exception:
        pytest.skip("git indisponible")
    assert git.is_repo(root) is True
    (tmp_path / "f.py").write_text("x\n", encoding="utf-8")
    # commit dry-run n'écrit pas
    dry = git.commit(root, "init", confirm=False)
    assert dry["dry_run"] is True
    done = git.commit(root, "init", confirm=True)
    assert done["ok"] is True
    assert "f.py" not in git.status(root)["status"]  # tout est committé


def test_editor_endpoints(client, tmp_path):
    root = str(tmp_path)
    r = client.post("/v1/code-intelligence/write",
                    json={"root": root, "path": "z.py", "content": "print(1)\n"})
    assert r.status_code == 200 and r.json()["dry_run"] is True
    r = client.post("/v1/code-intelligence/write",
                    json={"root": root, "path": "z.py", "content": "print(1)\n", "confirm": True})
    assert r.json()["written"] is True
    # garde-fou traversal -> 409
    r = client.post("/v1/code-intelligence/write",
                    json={"root": root, "path": "../x.py", "content": "x", "confirm": True})
    assert r.status_code == 409


def test_write_edit_tools_registered():
    from ai_engine.modules.tools.registry import get_tool_registry
    names = get_tool_registry().names()
    assert "code_write" in names and "code_edit" in names

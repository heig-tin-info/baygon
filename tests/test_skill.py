"""The Claude Code skill shipped with Baygon."""

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest
from typer.testing import CliRunner
import yaml

from baygon import skill
from baygon.__main__ import app
from baygon.schema import Schema

ROOT = Path(__file__).resolve().parent.parent


def test_skill_frontmatter() -> None:
    text = (skill.skill_source() / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, "SKILL.md must start with a YAML frontmatter"
    meta = yaml.safe_load(match.group(1))
    assert meta["name"] == "baygon"
    assert 50 < len(meta["description"]) <= 1024
    assert len(text.splitlines()) < 500


def test_skill_yaml_examples_are_valid() -> None:
    """Every complete example of the skill must pass the schema."""
    checked = 0
    for path in skill.skill_source().glob("*.md"):
        for block in re.findall(r"```yaml\n(.*?)```", path.read_text("utf-8"), re.S):
            data = yaml.safe_load(block)
            if isinstance(data, dict) and "tests" in data:
                Schema(data)
                checked += 1
    assert checked >= 5


def test_plugin_and_marketplace_manifests() -> None:
    plugin = json.loads(
        (ROOT / "plugins/baygon/.claude-plugin/plugin.json").read_text()
    )
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert plugin["name"] == "baygon"
    (entry,) = market["plugins"]
    assert entry["name"] == plugin["name"]
    # Released by .github/workflows/claude-plugin.yml from plugins/baygon,
    # with the version of the release: no version on master.
    assert entry["source"] == {
        "source": "github",
        "repo": "heig-tin-info/baygon",
        "ref": "claude-plugin",
    }
    assert "version" not in plugin
    assert (ROOT / "plugins/baygon/skills/baygon/SKILL.md").is_file()


def test_install_for_user_and_project(tmp_path: Path) -> None:
    home, project = tmp_path / "home", tmp_path / "project"
    user_dir = skill.install_skill("user", home=home)
    assert user_dir == home / ".claude/skills/baygon"
    project_dir = skill.install_skill("project", cwd=project)
    assert project_dir == project / ".claude/skills/baygon"
    for directory in (user_dir, project_dir):
        assert (directory / "SKILL.md").is_file()
        assert (directory / "reference.md").is_file()


def test_install_replaces_an_old_copy_only(tmp_path: Path) -> None:
    target = tmp_path / "skills"
    installed = skill.install_skill(str(target))
    (installed / "stale.md").write_text("old", encoding="utf-8")
    skill.install_skill(str(target))
    assert not (installed / "stale.md").exists()

    foreign = tmp_path / "other" / "baygon"
    foreign.mkdir(parents=True)
    (foreign / "notes.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(FileExistsError):
        skill.install_skill(str(tmp_path / "other"))
    assert (foreign / "notes.txt").read_text(encoding="utf-8") == "mine"


def test_missing_skill_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(skill, "_PACKAGE_DIR", tmp_path / "pkg")
    with pytest.raises(FileNotFoundError):
        skill.skill_source()


def test_cli_install_skill(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--install-skill", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "Baygon skill installed in" in result.output
    assert (tmp_path / "baygon" / "SKILL.md").is_file()

    (tmp_path / "x" / "baygon").mkdir(parents=True)
    result = runner.invoke(app, ["--install-skill", str(tmp_path / "x")])
    assert result.exit_code == 1
    assert "not a Baygon skill" in result.output

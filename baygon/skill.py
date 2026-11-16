"""Install the Baygon skill for Claude Code.

Claude Code loads skills from ``~/.claude/skills/<name>/`` (all projects) and
``.claude/skills/<name>/`` (one project). The skill ships with the package and
is copied there on request with ``baygon --install-skill user|project``.
"""

from __future__ import annotations

from pathlib import Path
import shutil

SKILL_NAME = "baygon"

_PACKAGE_DIR = Path(__file__).resolve().parent


def skill_source() -> Path:
    """Return the directory holding the skill files (``SKILL.md``...)."""
    candidates = (
        _PACKAGE_DIR / "skill",  # Installed wheel
        _PACKAGE_DIR.parent / "plugins" / "baygon" / "skills" / SKILL_NAME,  # Checkout
    )
    for candidate in candidates:
        if (candidate / "SKILL.md").is_file():
            return candidate
    raise FileNotFoundError("The Baygon skill files are missing from the package.")


def skills_directory(
    scope: str, *, cwd: Path | None = None, home: Path | None = None
) -> Path:
    """Return the skills directory for ``user``, ``project`` or a given path."""
    if scope == "user":
        return (home or Path.home()) / ".claude" / "skills"
    if scope == "project":
        return (cwd or Path.cwd()) / ".claude" / "skills"
    return Path(scope).expanduser()


def install_skill(
    scope: str, *, cwd: Path | None = None, home: Path | None = None
) -> Path:
    """Copy the skill into the skills directory of ``scope``.

    Installing again replaces a previous copy of the Baygon skill, but never a
    directory that holds something else.

    Returns:
        The directory the skill was installed in.
    """
    source = skill_source()
    destination = skills_directory(scope, cwd=cwd, home=home) / SKILL_NAME
    if destination.exists():
        marker = destination / "SKILL.md"
        if not marker.is_file() or f"name: {SKILL_NAME}" not in marker.read_text(
            encoding="utf-8"
        ):
            raise FileExistsError(
                f"'{destination}' exists and is not a Baygon skill, not replacing it."
            )
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return destination

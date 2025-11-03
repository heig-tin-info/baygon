"""Automation sessions powered by Nox and uv."""

import nox


PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]

nox.options.sessions = ["lint", "tests"]
nox.options.default_venv_backend = "uv"


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite under multiple Python versions."""
    session.install(".[test]")
    session.run("pytest", *session.posargs)


@nox.session
def lint(session: nox.Session) -> None:
    """Run static analysis."""
    session.install(".[lint]")
    session.run("ruff", "check", ".")
    session.run("black", "--check", ".")


@nox.session
def docs(session: nox.Session) -> None:
    """Build the documentation."""
    session.install(".[docs]")
    session.run("mkdocs", "build", "--strict")

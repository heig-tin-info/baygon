"""High-level services for loading and running Baygon suites."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .config.loader import (
    discover_config,
    load_config as load_config_model,
    load_config_dict,
)
from .core.models import SuiteModel, build_suite_model
from .error import ConfigError
from .runtime.runner import BaygonRunner, RunReport
from .schema import Schema
from .score import compute_points


def find_testfile(path: str | Path | None = None) -> Path | None:
    """Return the path to the first Baygon configuration file found."""
    try:
        return discover_config(path)
    except ConfigError:
        return None


def load_config(path: str | Path | None = None) -> Mapping[str, Any]:
    """Load and validate a configuration file (YAML or JSON)."""
    return load_config_dict(path)


@dataclass(frozen=True)
class SuiteContext:
    """Immutable bundle describing a suite ready to be executed."""

    config: Mapping[str, Any]
    model: SuiteModel
    base_dir: Path
    source_path: Path | None

    @property
    def name(self) -> str:
        return str(self.config.get("name", ""))

    @property
    def version(self) -> int | None:
        version = self.config.get("version")
        return int(version) if version is not None else None

    def create_runner(
        self,
        *,
        executable: str | Path | None = None,
        runner_factory: Callable[..., BaygonRunner] = BaygonRunner,
    ) -> BaygonRunner:
        """Return a runner configured for this suite."""
        return runner_factory(
            self.model,
            base_dir=self.base_dir,
            executable=executable,
        )


class SuiteBuilder:
    """Build immutable suite models from validated configuration mappings."""

    def __init__(
        self,
        *,
        model_factory: Callable[[Mapping[str, Any]], SuiteModel] = build_suite_model,
    ) -> None:
        self._model_factory = model_factory

    def build(self, config: Mapping[str, Any]) -> SuiteModel:
        """Return a SuiteModel derived from the given configuration."""
        return self._model_factory(config)


class SuiteLoader:
    """Load suite configurations from files or raw mappings."""

    def __init__(
        self,
        *,
        schema_loader: Callable[[Any], MutableMapping[str, Any]] = Schema,
        builder: SuiteBuilder | None = None,
    ) -> None:
        self._schema_loader = schema_loader
        self._builder = builder or SuiteBuilder()

    def from_mapping(
        self,
        data: Mapping[str, Any] | MutableMapping[str, Any],
        *,
        cwd: str | Path | None = None,
    ) -> SuiteContext:
        """Validate a raw mapping and build its execution context."""
        validated = self._schema_loader(data)
        compute_points(validated)

        base_dir = Path(cwd) if cwd is not None else Path.cwd()
        model = self._builder.build(validated)

        return SuiteContext(
            config=validated,
            model=model,
            base_dir=base_dir.resolve(),
            source_path=None,
        )

    def from_path(
        self,
        path: str | Path | None,
    ) -> SuiteContext:
        """Load configuration from disk and build its execution context."""
        config_path = discover_config(path)
        config = load_config_dict(config_path)
        model = load_config_model(config_path)
        base_dir = config_path.parent

        return SuiteContext(
            config=config,
            model=model,
            base_dir=base_dir.resolve(),
            source_path=config_path,
        )

    def load(
        self,
        *,
        data: Mapping[str, Any] | MutableMapping[str, Any] | None = None,
        path: str | Path | None = None,
        cwd: str | Path | None = None,
    ) -> SuiteContext:
        """Load a suite configuration from a mapping or a path."""
        if data is not None and path is not None:
            raise ValueError("Provide either 'data' or 'path', not both.")

        if data is not None:
            return self.from_mapping(data, cwd=cwd)

        return self.from_path(path)


class SuiteExecutor:
    """Execute suites described by `SuiteContext`."""

    def __init__(
        self,
        *,
        runner_factory: Callable[..., BaygonRunner] = BaygonRunner,
    ) -> None:
        self._runner_factory = runner_factory

    def run(
        self,
        context: SuiteContext,
        *,
        executable: str | Path | None = None,
        limit: int = -1,
    ) -> RunReport:
        """Run the suite described by the provided context."""
        runner = context.create_runner(
            executable=executable,
            runner_factory=self._runner_factory,
        )
        return runner.run(limit=limit)


class SuiteService:
    """Facade coordinating loading and execution of Baygon suites."""

    def __init__(
        self,
        loader: SuiteLoader | None = None,
        executor: SuiteExecutor | None = None,
    ) -> None:
        self._loader = loader or SuiteLoader()
        self._executor = executor or SuiteExecutor()

    def load(
        self,
        *,
        data: Mapping[str, Any] | MutableMapping[str, Any] | None = None,
        path: str | Path | None = None,
        cwd: str | Path | None = None,
    ) -> SuiteContext:
        """Return a validated suite context without running it."""
        return self._loader.load(data=data, path=path, cwd=cwd)

    def run(
        self,
        *,
        data: Mapping[str, Any] | MutableMapping[str, Any] | None = None,
        path: str | Path | None = None,
        cwd: str | Path | None = None,
        executable: str | Path | None = None,
        limit: int = -1,
    ) -> RunReport:
        """Load and execute a suite in one call."""
        context = self._loader.load(data=data, path=path, cwd=cwd)
        return self._executor.run(
            context,
            executable=executable,
            limit=limit,
        )

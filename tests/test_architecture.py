"""Guards for the layering: routers -> services -> repositories -> models.

These fail when someone breaks the dependency rules, long before the app does.
"""

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"

# Layers that must not know about the web framework.
FRAMEWORK_FREE = ["services", "repositories", "models", "schemas", "core", "mailer"]

# layer -> layers it must not import from (everything above it).
FORBIDDEN_IMPORTS = {
    "models": ["repositories", "services", "routers", "schemas"],
    "repositories": ["services", "routers", "schemas"],
    "core": ["repositories", "services", "routers", "schemas"],
    "schemas": ["repositories", "services", "routers"],
    "services": ["routers"],
    "mailer": ["repositories", "services", "routers"],
}

# Code that reaches the database must go through a repository.
NO_DIRECT_SQL = ["services", "routers", "worker"]
SQL_METHODS = {"query", "execute", "add", "add_all", "delete", "get"}


def python_files(layer: str):
    return sorted((APP / layer).rglob("*.py"))


def imported_modules(path: Path) -> list[str]:
    modules = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            modules += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
            # "from app import models" names a layer too
            if node.module == "app":
                modules += [f"app.{alias.name}" for alias in node.names]
    return modules


@pytest.mark.parametrize("layer", FRAMEWORK_FREE)
def test_layer_does_not_import_the_web_framework(layer):
    offenders = [
        f"{path.relative_to(APP)} imports {module}"
        for path in python_files(layer)
        for module in imported_modules(path)
        if module.split(".")[0] in {"fastapi", "starlette"}
    ]
    assert not offenders, offenders


@pytest.mark.parametrize("layer", sorted(FORBIDDEN_IMPORTS))
def test_layer_does_not_import_the_layers_above_it(layer):
    forbidden = tuple(f"app.{name}" for name in FORBIDDEN_IMPORTS[layer])
    offenders = [
        f"{path.relative_to(APP)} imports {module}"
        for path in python_files(layer)
        for module in imported_modules(path)
        if module in forbidden or module.startswith(tuple(f"{f}." for f in forbidden))
    ]
    assert not offenders, offenders


@pytest.mark.parametrize("layer", NO_DIRECT_SQL)
def test_only_repositories_talk_to_the_database(layer):
    offenders = []
    for path in python_files(layer):
        for node in ast.walk(ast.parse(path.read_text())):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in SQL_METHODS
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "db"
            ):
                offenders.append(
                    f"{path.relative_to(APP)}:{node.lineno} db.{node.func.attr}()"
                )
    assert not offenders, offenders


def mentions_http_exception(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "HTTPException"
    if isinstance(node, ast.ImportFrom):
        return any(alias.name == "HTTPException" for alias in node.names)
    return False


def test_errors_are_raised_as_app_errors_not_http_exceptions():
    offenders = [
        str(path.relative_to(APP))
        for path in sorted(APP.rglob("*.py"))
        if any(
            mentions_http_exception(n) for n in ast.walk(ast.parse(path.read_text()))
        )
    ]
    assert not offenders, offenders

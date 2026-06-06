---
name: refactor-module
description: Systematically refactor a Python module for PEP8, clean code, and modularity
argument-hint: <folder-path>
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Refactor Module

Systematically refactor all Python files in `$ARGUMENTS` to enforce PEP 8, clean code,
modularity, and modern Python best practices.

## Scope Rules

- **Only** modify files inside `$ARGUMENTS`. Never touch files outside that path.
- Shared utilities extracted during deduplication go into a `common.py` or `utils.py`
  **within** the target folder — never into a parent or sibling package.
- Imports from outside the target folder (e.g. `config`, `core`, `helpers`) stay unchanged.

## Procedure

### 1. Scan

Use Glob `$ARGUMENTS/**/*.py` to list every Python file. Read each file and note:
line count, existing type hints, imports, docstrings, logging usage, Pydantic patterns.

### 2. Apply Quality Passes (in order)

Execute these passes sequentially on every file within scope:

#### Pass 1 — Type Hints (PEP 484)

- Add parameter and return type annotations to **all** functions and methods.
- Use `typing` module types: `Dict`, `List`, `Optional`, `Any`, `Union`, `Callable`, etc.
- For FastAPI route handlers, add response type annotations (`-> JSONResponse`, `-> HTMLResponse`, etc.).
- For async generators, use `AsyncGenerator[YieldType, SendType]`.

#### Pass 2 — Pydantic v2 Migration

- Replace all `.dict()` calls with `.model_dump()`.
- Replace deprecated `class Config:` inner classes with `model_config = ConfigDict(...)`.
- Ensure mutable or computed defaults use `Field(default_factory=...)` instead of bare expressions
  (e.g. `created: int = int(time.time())` is a bug — it evaluates once at import).
- Import `ConfigDict` and `Field` from `pydantic` as needed.

#### Pass 3 — Logging Consistency

- Replace `print()` calls used for debug/info output with `logger.debug()` or `logger.info()`.
- Use the project's established logger: `from core.app_factory import logger`.
- Never silently swallow exceptions (`except Exception: pass`). At minimum log them.

#### Pass 4 — Docstrings

- Add concise Google-style docstrings to all public functions, classes, and modules.
- One summary line, plus `Args:` / `Returns:` sections only when parameters are non-obvious.
- Do **not** add docstrings to trivial `__init__.py` re-exports.
- Keep comments concise — explain *why*, not *what*.

#### Pass 5 — Unused Imports

- Remove any imports that are not referenced anywhere in the file.

#### Pass 6 — Pydantic Field Descriptions

- Add `Field(description="...")` to Pydantic model fields, especially on public-facing API schemas.
- Keep descriptions short and factual.

#### Pass 7 — Code Deduplication

- Identify functions or logic blocks duplicated **within** the target folder scope.
- Extract shared code into a `common.py` (or `utils.py`) **within the same folder**.
- Use parameters or callbacks to handle minor variations between call sites.
- Do **not** extract code if the duplication is trivial (< 5 lines) or if merging
  would lose type safety (e.g. functions returning different Pydantic model types).

#### Pass 8 — Error Handling

- Replace bare `except:` with typed `except Exception as exc:`.
- Replace silent `except Exception: pass` with at minimum `except Exception as exc: logger.debug(...)`.
- Ensure consistent error response patterns within the folder.

#### Pass 9 — Named Constants

- Replace magic numbers and hardcoded string literals with descriptive module-level constants.
- Use UPPER_SNAKE_CASE naming.
- Examples: `STREAM_CHUNK_SIZE = 3`, `DEFAULT_TEMPERATURE = 0.7`.

### 3. Verify

After all edits, run a syntax check on every modified file:

```bash
python -c "import ast; ast.parse(open('<file>').read())"
```

Report any failures immediately and fix them before continuing.

### 4. Summary

Output a markdown table with columns: **File**, **Changes Made**, **Lines Before → After**.

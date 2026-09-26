"""Fail closed on risky staged files and validate the tracked worktree."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
DATA_SUFFIXES = {".csv", ".parquet", ".duckdb", ".jsonl"}
PRIVATE_KEY = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
SECRET_PATTERNS = (
    PRIVATE_KEY,
    re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(rb"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}\b"),
)
MAX_BYTES = 512 * 1024


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(REPOSITORY), *args],
        check=True,
        capture_output=True,
    ).stdout


def _staged_paths() -> list[str]:
    return [
        path.decode("utf-8", errors="surrogateescape")
        for path in _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split(b"\0")
        if path
    ]


def _tracked_paths() -> list[str]:
    return [
        path.decode("utf-8", errors="surrogateescape")
        for path in _git("ls-files", "-z").split(b"\0")
        if path
    ]


def _index_bytes(path: str) -> bytes:
    return _git("show", f":{path}")


def _data_file_errors(paths: list[str]) -> list[str]:
    return [
        path
        for path in paths
        if Path(path).suffix.lower() in DATA_SUFFIXES
        and not path.replace("\\", "/").startswith("tests/fixtures/")
    ]


def _secret_errors(paths: list[str]) -> list[str]:
    return [
        path
        for path in paths
        if (
            Path(path).name == ".env"
            or ".terraform" in Path(path).parts
            or re.search(r"\.(?:tfvars(?:\.json)?|tfstate(?:\..*)?|tfplan|backend\.hcl)$", path)
            or any(pattern.search(_index_bytes(path)) for pattern in SECRET_PATTERNS)
        )
    ]


def _large_file_errors(paths: list[str], staged: bool) -> list[str]:
    errors: list[str] = []
    for path in paths:
        if staged:
            size = int(_git("cat-file", "-s", f":{path}").decode("ascii"))
        else:
            local_path = REPOSITORY / path
            if not local_path.is_file():
                continue
            size = local_path.stat().st_size
        if size > MAX_BYTES:
            errors.append(path)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--data-files", action="store_true")
    group.add_argument("--secrets", action="store_true")
    group.add_argument("--large-files", action="store_true")
    group.add_argument("--working-tree", action="store_true")
    args = parser.parse_args()

    paths = _tracked_paths() if args.working_tree else _staged_paths()
    errors: list[str] = []
    if args.data_files:
        errors = _data_file_errors(paths)
    elif args.secrets:
        errors = _secret_errors(paths)
    elif args.large_files:
        errors = _large_file_errors(paths, staged=True)
    elif args.working_tree:
        errors = _data_file_errors(paths)
        errors.extend(_secret_errors(paths))
        errors.extend(_large_file_errors(paths, staged=False))

    if errors:
        for path in sorted(set(errors)):
            sys.stderr.write(f"BLOCKED: {path}\n")
        return 1
    sys.stdout.write("staged-file policy passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import os
import subprocess
import sys
from pathlib import Path
from socket import socket

import pytest

assets_path = Path(__file__).parent / "assets"


def _run_fastapi(*args: str) -> str:
    with socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = str(sock.getsockname()[1])
    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "fastapi_cli",
            "run",
            "--host=127.0.0.1",
            f"--port={port}",
            *args,
        ],
        cwd=assets_path,
        env={**os.environ, "FASTAPI_PORT": port},
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    return result.stderr or ""


def test_syntax_error() -> None:
    output = _run_fastapi("errors/syntax.py")
    assert "Uncaught SyntaxError" in output, "TraceRite syntax error should be printed"
    assert "(most recent call last)" not in output, (
        "Built-in or Typer traceback should not be printed"
    )


@pytest.mark.parametrize("workers", [1, 2], ids=["single-process", "multi-process"])
def test_request(workers: int) -> None:
    output = _run_fastapi("errors/request.py", "--workers", str(workers))
    assert "from previous" in output, "TraceRite traceback should be printed"
    assert "(most recent call last)" not in output, (
        "Built-in or Typer traceback should not be printed"
    )

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from configparser import ConfigParser
from contextlib import contextmanager
from typing import Dict, Generator, NamedTuple, Optional, cast

from .printer import Printer


@contextmanager
def temp_mypy_ini(**kwargs):
    cfg = ConfigParser()
    cfg.add_section("mypy")
    for k, v in kwargs.items():
        cfg.set("mypy", k, v)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", prefix="mypy_") as f:
        cfg.write(f)
        f.flush()
        yield f.name


def run_mypy(cmd, **kwargs) -> str:
    Printer.info(f"> {cmd}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        encoding="utf-8",
        text=True,
        **kwargs,
    )
    # https://github.com/python/mypy/issues/6003#issue-387302948
    if result.returncode == 2:
        Printer.error(result.stderr)
        sys.exit(result.returncode)
    else:
        return cast(str, result.stdout)


MYPY_OPTS = dict(
    ignore_missing_imports="false",
    no_color_output="true",
    no_pretty="true",
    no_error_summary="true",
    show_error_codes="true",
)


def get_mypy_output(
    args: str = ".", mypy_opts: Dict[str, str] = MYPY_OPTS
) -> Generator[MypyLine, None, None]:
    with temp_mypy_ini(**mypy_opts) as mypy_ini:
        cmd = f"mypy --config-file {mypy_ini} {args}"
        stdout = run_mypy(cmd, shell=True)
        for line in stdout.split("\n"):
            line = line.strip()
            if len(line):
                parsed_line = parse_mypy_line(line)
                if parsed_line is not None:
                    yield parsed_line


class MypyLine(NamedTuple):
    type: str
    errtxt: str
    code: Optional[str]


MYPY_LINE_RE = re.compile(
    r"""^
     .*?:                         # file name
     \d+:                         # line number
     \s*(?P<type>error|note):\s*  # type
     (?P<errtxt>.*?)              # errtxt
     (\s+\[(?P<code>.*?)\])?      # code
     $
     """,
    re.X,
)


def parse_mypy_line(line: str) -> Optional[MypyLine]:
    if result := MYPY_LINE_RE.search(line):
        return MypyLine(
            result.group("type"), result.group("errtxt"), result.group("code")
        )
    else:
        return None

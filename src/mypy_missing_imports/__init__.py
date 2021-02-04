import sys
from pathlib import Path
from typing import Optional

import snoop
import typer

from .missing_imports import missing_imports
from .output import print_config, update_file
from .printer import Printer

snoop.install()


def do(
    config_file: Optional[Path] = typer.Argument(
        None,
        help="Config file, usually mypy.ini. (Optional, will print to stdout if not provided)",
    )
):
    imps = missing_imports()
    if not len(imps):
        return

    Printer.info(f"> Found missing imports for {','.join(imps)}")

    if config_file is None:
        print_config(imps)
    elif config_file.suffix == ".ini":
        update_file(imps, config_file, fmt="ini")
    elif config_file.suffix == ".toml":
        update_file(imps, config_file, fmt="toml")
    else:
        Printer.error(
            f"Unsupported file format for {config_file}, only ini/toml are supported"
        )
        sys.exit(1)


def main():
    typer.run(do)

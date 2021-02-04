from __future__ import annotations

import io
import re
from abc import abstractmethod
from configparser import ConfigParser
from pathlib import Path
from typing import Generic, List, Literal, Set, Type, TypeVar

import tomlkit

from .printer import Printer

MYPY_SECTION_CONTENTS = {"ignore_missing_imports": "true"}


def update_file(missing_imports: Set[str], f: Path, fmt: Literal["ini", "toml"]):
    upd: ConfUpdater
    if fmt == "ini":
        upd = IniUpdater.from_file(f)
    elif fmt == "toml":
        upd = TomlUpdater.from_file(f)

    updated = update_conf(upd, missing_imports)
    f.write_text(updated)
    Printer.info(f"> Updated file {f}")


class SafeConfigParser(ConfigParser):
    """Preserve comments. Won't preserve spaces"""

    def __init__(self, **kwargs):
        # https://stackoverflow.com/a/52306763
        super().__init__(allow_no_value=True, comment_prefixes=("/",), **kwargs)

    def optionxform(self, x):
        return x


def print_config(missing_imports: Set[str]):
    upd = IniUpdater(SafeConfigParser())
    new_sections = get_conf_sections(missing_imports)
    for a in new_sections:
        upd.add_to_section(a, **MYPY_SECTION_CONTENTS)
    Printer.raw(str(upd))


def update_conf(upd: ConfUpdater, missing_imports: Set[str]) -> str:
    existing_sections = set(
        s for s in upd.get_all_sections() if is_mypy_section_name(s)
    )
    new_sections = get_conf_sections(missing_imports)
    remove = existing_sections.difference(new_sections)
    for r in remove:
        upd.remove_from_section(r, **MYPY_SECTION_CONTENTS)
    for a in new_sections:
        upd.add_to_section(a, **MYPY_SECTION_CONTENTS)
    return str(upd)


def get_conf_sections(missing_imports: Set[str]) -> List[str]:
    return [mypy_section_name(m) for m in sorted(top_level_modules(missing_imports))]


def top_level_modules(modules: Set[str]) -> Set[str]:
    return set(m.split(".")[0] for m in modules)


def mypy_section_name(module: str) -> str:
    return f"mypy-{module}.*"


def is_mypy_section_name(s: str) -> bool:
    return re.match("mypy-.*", s) is not None


T = TypeVar("T")
C = TypeVar("C")


class ConfUpdater(Generic[T]):
    def __init__(self, conf: T):
        self.conf = conf

    @classmethod
    @abstractmethod
    def from_file(cls: Type[C], f: Path) -> C:
        pass

    @abstractmethod
    def get_all_sections(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def add_to_section(self, section: str, **contents):
        raise NotImplementedError

    @abstractmethod
    def remove_from_section(self, section: str, **contents):
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError


class TomlUpdater(ConfUpdater[tomlkit.toml_document.TOMLDocument]):
    @classmethod
    def from_file(cls, f: Path) -> TomlUpdater:
        return TomlUpdater(tomlkit.parse(f.read_text()))

    def get_all_sections(self):
        return self.conf.keys()

    def add_to_section(self, section: str, **contents):
        if section not in self.conf:
            self.conf[section] = tomlkit.table()
        for k, v in contents.items():
            self.conf[section][k] = v

    def remove_from_section(self, section: str, **contents):
        assert section in self.conf
        for k, v in contents.items():
            self.conf[section].remove(k)
        if not len(self.conf[section]):
            self.conf.remove(section)

    def __str__(self):
        return tomlkit.dumps(self.conf)


class IniUpdater(ConfUpdater[SafeConfigParser]):
    @classmethod
    def from_file(cls, f: Path) -> IniUpdater:
        cfg = SafeConfigParser()
        cfg.read_string(f.read_text())
        return IniUpdater(cfg)

    def get_all_sections(self):
        return self.conf.sections()

    def add_to_section(self, section: str, **contents):
        if not self.conf.has_section(section):
            self.conf.add_section(section)
        for k, v in contents.items():
            self.conf.set(section, k, v)

    def remove_from_section(self, section: str, **contents):
        assert self.conf.has_section(section)
        for k, v in contents.items():
            self.conf.remove_option(section, k)
        if not len(self.conf.items(section)):
            self.conf.remove_section(section)

    def __str__(self):
        f = io.StringIO()
        self.conf.write(f)
        return f.getvalue()

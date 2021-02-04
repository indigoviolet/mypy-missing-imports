import re
from typing import Optional, Set

from .parse_mypy import get_mypy_output

IMPORT_ERROR_RES = [
    # "Skipping analyzing 'google.cloud': found module but no type hints or library stubs"
    re.compile(
        r"""
        Skipping\sanalyzing\s
        '(?P<module>.*?)'
        :\sfound\smodule\sbut\sno\stype\shints\sor\slibrary\sstubs
        """,
        re.X,
    ),
    # "Cannot find implementation or library stub for module named 'fastai2.learner'"
    re.compile(
        r"""
        Cannot\sfind\simplementation\sor\slibrary\sstub\sfor\smodule\snamed\s
        '(?P<module>.*?)'
        """,
        re.X,
    ),
]


def missing_imports() -> Set[str]:
    import_errors = (line for line in get_mypy_output() if line.code == "import")
    modules = (parse_import_error_module(e.errtxt) for e in import_errors)
    return set(m for m in modules if m is not None)


def parse_import_error_module(line: str) -> Optional[str]:
    for r in IMPORT_ERROR_RES:
        if m := r.search(line):
            return m.group("module")
    return None

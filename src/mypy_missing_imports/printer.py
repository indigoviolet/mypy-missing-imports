from rich.console import Console
from rich.markup import escape
from rich.theme import Theme

theme = {"error": "red", "success": "green", "info": "blue"}

console = Console(theme=Theme(theme, inherit=False))


class PrinterMeta(type):
    def __getattr__(self, name):
        assert name in theme
        return lambda x: console.print(escape(x), style=name)


class Printer(metaclass=PrinterMeta):
    @classmethod
    def raw(cls, s: str):
        console.print(escape(s))

from rich.console import Console
from rich.syntax import Syntax


def rich_print_json(items: str, message: str, theme: str = "dracula", line_numbers: bool = True):
    console = Console()
    console.print(f"\n-------------------------------- {message} --------------------------------")
    syntax = Syntax(items, "json", theme=theme, line_numbers=line_numbers)
    console.print(syntax, "\n")

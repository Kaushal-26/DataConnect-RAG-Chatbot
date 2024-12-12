import json
from typing import Any, Dict

from rich.console import Console
from rich.syntax import Syntax


def print_items(items: Dict[str, Any], message: str, theme: str = "dracula", line_numbers: bool = True):
    console = Console()
    console.print(f"\n-------------------------------- {message} --------------------------------")
    syntax = Syntax(json.dumps(items, indent=4), "json", theme=theme, line_numbers=line_numbers)
    console.print(syntax, "\n")

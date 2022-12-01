from .base import BasePrompt

from rich import print
import rich.table


class help(BasePrompt):
    """Display help documentation."""

    @property
    def usage(self):
        return "help [COMMAND]"

    def process(self, cmd, *parts):
        if not parts:
            print("Available Commands:")
            table = rich.table.Table()
            table.add_column("Command", style="yellow", no_wrap=True)
            table.add_column("Description")
            for name, obj in self.parent.commands.items():
                if name.startswith('_'):
                    continue
                table.add_row(getattr(obj, 'usage', name), obj.__doc__)
            print(table)
        else:
            print(f"Help for {' '.join(parts)}:")

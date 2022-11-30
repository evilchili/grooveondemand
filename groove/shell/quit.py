from .base import BasePrompt


class quit(BasePrompt):
    """Exit the interactive shell."""

    def process(self, cmd, *parts):
        raise SystemExit()

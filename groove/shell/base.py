from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion


class BasePrompt(Completer):

    def __init__(self, manager=None, parent=None):
        super(BasePrompt, self).__init__()

        if (not manager and not parent):
            raise RuntimeError("Must define either a database manager or a parent object.")

        self._prompt = ''
        self._values = []
        self._parent = parent
        self._manager = manager

    @property
    def usage(self):
        return self.__class__.__name__

    @property
    def help_text(self):
        return self.__doc__

    @property
    def manager(self):
        if self._manager:
            return self._manager
        elif self._parent:
            return self._parent.manager

    @property
    def parent(self):
        return self._parent

    @property
    def prompt(self):
        return self._prompt

    @property
    def values(self):
        return self._values

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        found = False
        for value in self.values:
            if word in value:
                found = True
                yield Completion(value, start_position=-len(word))
        if not found:
            try:
                for result in self.default_completer(document, complete_event):
                    yield result
            except NotImplementedError:
                pass

    def start(self, cmd=''):
        while True:
            if not cmd:
                cmd = prompt(f'{self.prompt} ', completer=self)
            if not cmd:
                return
            cmd, *parts = cmd.split()
            if not self.process(cmd, *parts):
                return
            cmd = ''

    def default_completer(self, document, complete_event):
        raise NotImplementedError()

    def process(self, cmd, *parts):
        raise NotImplementedError()
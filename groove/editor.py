import logging
import os
import subprocess
import yaml

from tempfile import NamedTemporaryFile


EDITOR_TEMPLATE = """
{name}:
  description: {description}
  entries:
    {entries}

# ------------------------------------------------------------------------------
#
# Groove On Demand Playlist Editor
#
# This file is in YAML format. Blank lines and lines beginning with # are
# ignored. Here's a complete example:
#
#   My Awesome Jams, Vol. 2:
#     description: |
#       These jams are totally awesome, yo.
#       Totally.
#
#       yo.
#     entries:
#       - Beastie Boys - Help Me, Ronda
#       - Bob and Doug McKenzie - Messiah (Hallelujah Eh)
#
"""


class PlaylistEditor:
    """
    A custom ConfigParser that only supports specific headers and ignores all other square brackets.
    """
    def __init__(self):
        self._path = None

    @property
    def path(self):
        if not self._path:
            self._path = NamedTemporaryFile(prefix='groove_on_demand-', delete=False)
        return self._path

    def edit(self, playlist):
        with self.path as fh:
            fh.write(playlist.as_yaml.encode())
        subprocess.check_call([os.environ['EDITOR'], self.path.name])
        edits = self.read()
        self.cleanup()
        return edits

    def read(self):
        with open(self.path.name, 'rb') as fh:
            return yaml.safe_load(fh)

    def cleanup(self):
        if self._path:
            os.unlink(self._path.name)
            self._path = None

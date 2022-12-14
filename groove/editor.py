import logging
import os
import subprocess
import yaml

from yaml.scanner import ScannerError
from groove.exceptions import PlaylistValidationError


from tempfile import NamedTemporaryFile


EDITOR_TEMPLATE = """
{name}:
  description: |
{description}
  entries:
{entries}

# ------------------------------------------------------------------------------
#
# Groove On Demand Playlist Editor
#
# This file is in YAML format. Blank lines and lines beginning with # are
# ignored, and the following structure is expected:
#
# PLAYLIST_TITLE:
#  description: STRING_DESCRIPTION
#  entries:
#    - TRACK_ARTIST - TRACK_TITLE
#    ...
#
# Here's a complete example, with a multi-line description:
#
#   My Awesome Jams, Vol. 2:
#     description: |
#       These jams are totally awesome, yo.
#       Totally.
#
#       yo.
#     entries:
#       - Beastie Boys: Help Me, Rhonda
#       - Bob and Doug McKenzie: Messiah (Hallelujah Eh)
#
# Tracks can be reordered or removed. You can also add a track, if the artist/title
# combination exactly matches precisely one Track entry your database. Searches are
# case-sensitive.
#
# Playlists can be renamed and descriptions can be updated or removed. If you rename a
# playlist, its slug will be regnenerated, breaking previous web links to said playlist.
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
        try:
            with self.path as fh:
                fh.write(playlist.as_yaml.encode())
            subprocess.check_call([os.environ.get('EDITOR', 'vim'), self.path.name])
        except (IOError, OSError, FileNotFoundError) as e:
            logging.error(e)
            raise RuntimeError("Could not invoke the editor! If the error persists, try enabling DEBUG mode.")
        try:
            edits = self.read()
        except ScannerError:
            raise PlaylistValidationError(
                f"An error occurred when importing the playlist definition. This is "
                f"typically the result of a YAML syntax error; you can inspect the "
                f"source for errors at {self._path.name}."
            )
        self.cleanup()
        return edits

    def read(self):
        with open(self.path.name, 'rb') as fh:
            return yaml.safe_load(fh)

    def cleanup(self):
        if self._path:
            os.unlink(self._path.name)
            self._path = None

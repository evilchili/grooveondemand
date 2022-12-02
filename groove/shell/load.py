from .base import BasePrompt

from slugify import slugify

from groove.playlist import Playlist


class load(BasePrompt):
    """Create a new playlist."""

    @property
    def usage(self):
        return "load PLAYLIST_NAME"

    def process(self, cmd, *parts):
        name = ' '.join(parts)
        if not name:
            print(f"Usage: {self.usage}")
            return
        slug = slugify(name)
        self.parent._playlist = Playlist(
            slug=slug,
            name=name,
            session=self.manager.session,
            create_ok=True
        )
        print(self.parent.playlist.summary)
        return self.parent.commands['_playlist'].start()

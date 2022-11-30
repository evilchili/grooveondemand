from .base import BasePrompt

from slugify import slugify

from groove.playlist import Playlist


class create(BasePrompt):
    """Create a new playlist."""

    @property
    def usage(self):
        return "create PLAYLIST_NAME"

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
            create_if_not_exists=True
        )
        return self.parent.commands['_playlist'].start()

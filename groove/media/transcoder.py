import asyncio
import logging
import os
import subprocess

from typing import Union, List

import rich.repr

from rich.console import Console
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    SpinnerColumn,
    TimeRemainingColumn
)

import groove.path

from groove.exceptions import ConfigurationError


@rich.repr.auto(angular=True)
class Transcoder:
    """
    SYNOPSIS

    USAGE

    ARGS

    EXAMPLES

    INSTANCE ATTRIBUTES
    """

    def __init__(self, console: Union[Console, None] = None) -> None:
        self.console = console or Console()
        self._transcoded = 0
        self._processed = 0
        self._total = 0

    def transcode(self, sources: List) -> int:
        """
        Transcode the list of source files
        """
        count = len(sources)

        if not os.environ.get('TRANSCODER', None):
            raise ConfigurationError("Cannot transcode tracks without a TRANSCODR defined in your environment.")

        cache = groove.path.cache_root()
        if not cache.exists():
            cache.mkdir()

        async def _do_transcode(progress, task_id):
            tasks = set()
            for relpath in sources:
                self._total += 1
                progress.update(task_id, total=self._total)
                tasks.add(asyncio.create_task(self._transcode_one_track(relpath, progress, task_id)))
            progress.start_task(task_id)

        progress = Progress(
            TimeRemainingColumn(compact=True, elapsed_when_finished=True),
            BarColumn(bar_width=15),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%", justify="left"),
            TextColumn("[dim]|"),
            TextColumn("[title]{task.total:-6d}[/title] [b]total", justify="right"),
            TextColumn("[dim]|"),
            TextColumn("[title]{task.fields[transcoded]:-6d}[/title] [b]new", justify="right"),
            TextColumn("[dim]|"),
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )
        with progress:
            task_id = progress.add_task(
                f"[bright]Transcoding [link]{count} tracks[/link]...",
                transcoded=0,
                total=0,
                start=False
            )
            asyncio.run(_do_transcode(progress, task_id))
            progress.update(
                task_id,
                transcoded=self._transcoded,
                completed=self._total,
                description=f"[bright]Transcode of [link]{count} tracks[/link] complete!",
            )

    def _get_or_create_cache_dir(self, relpath):
        cached_path = groove.path.transcoded_media(relpath)
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        return cached_path

    def _run_transcoder(self, infile, outfile):
        cmd = []
        for part in os.environ['TRANSCODER'].split():
            if part == 'INFILE':
                cmd.append(str(infile))
            elif part == 'OUTFILE':
                cmd.append(str(outfile))
            else:
                cmd.append(part)

        output = ''
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.console.error(f"Transcoder failed with status {e.returncode}: {' '.join(cmd)}")
            self.console.error(output)

    async def _transcode_one_track(self, relpath, progress, task_id):
        """
        Transcode one track, if it isn't already cached.
        """
        self._processed += 1

        source_path = groove.path.media(relpath)
        if not source_path.exists():
            logging.error(f"Source does not exist: [link]{source_path}[/link].")
            return

        cached_path = self._get_or_create_cache_dir(relpath)
        if cached_path.exists():
            self.console.debug(f"Skipping existing [link]{cached_path}[/link].")
            return

        self.console.debug(f"Transcoding [link]{cached_path}[/link]")
        self._run_transcoder(source_path, cached_path)

        progress.update(
            task_id,
            transcoded=self._transcoded,
            processed=self._processed,
            description=f"[bright]Transcoded [link]{relpath}[/link]",
        )

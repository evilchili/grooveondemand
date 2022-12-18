import pytest

from groove.db.manager import database_manager
from groove.shell import interactive_shell
from unittest.mock import MagicMock


@pytest.fixture
def cmd_prompt(monkeypatch, in_memory_engine, db):
    with database_manager() as manager:
        manager._session = db
        yield interactive_shell.InteractiveShell(manager)


def response_factory(responses):
    return MagicMock(side_effect=responses + ([''] * 10))


@pytest.mark.parametrize('inputs, expected', [
    (['stats'], 'Database contains 4 playlists'),  # match the db fixture
])
def test_stats(monkeypatch, capsys, cmd_prompt, inputs, expected):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory(inputs))
    cmd_prompt.start()
    output = capsys.readouterr()
    assert expected in output.out


@pytest.mark.parametrize('inputs, expected', [
    (['quit'], SystemExit),
])
def test_quit(monkeypatch, capsys, cmd_prompt, inputs, expected):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory(inputs))
    with pytest.raises(expected):
        cmd_prompt.start()


def test_list(monkeypatch, capsys, cmd_prompt):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory(['list']))
    cmd_prompt.start()


@pytest.mark.parametrize('inputs', ['help', 'help list'])
def test_help(monkeypatch, capsys, cmd_prompt, inputs):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory([inputs]))
    cmd_prompt.start()


@pytest.mark.parametrize('inputs, expected', [
    (['load A New Playlist'], 'a-new-playlist'),
    (['new playlist'], 'new-playlist'),
    (['load'], '')
])
def test_load(monkeypatch, caplog, cmd_prompt, inputs, expected):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory(inputs))
    cmd_prompt.start()
    assert expected in caplog.text


def test_values(cmd_prompt):
    for cmd in [cmd for cmd in cmd_prompt.commands.keys() if not cmd.startswith('_')]:
        assert cmd in cmd_prompt.autocomplete_values


def test_playlist_usage(monkeypatch, cmd_prompt):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory([
        'load new playlist',
        'help'
    ]))
    cmd_prompt.start()


def test_playliest_edit(monkeypatch, cmd_prompt):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory([
        'load new playlist',
        'edit'
    ]))
    cmd_prompt.start()


def test_playlist_show(monkeypatch, cmd_prompt):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory([
        'load playlist one',
        'show'
    ]))
    cmd_prompt.start()


def test_playlist_add(monkeypatch, cmd_prompt):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory([
        'load playlist one',
        'add',
        '',
        'add',
        'UNKLE/Psyence Fiction/01 Guns Blazing (Drums of Death, Part 1).flac',
        '',
    ]))
    cmd_prompt.start()


def test_playlist_delete(monkeypatch, cmd_prompt):
    monkeypatch.setattr('groove.console.Console.prompt', response_factory([
        'load playlist one',
        'delete',
        '',
        'delete',
        'DELETE',
    ]))
    cmd_prompt.start()

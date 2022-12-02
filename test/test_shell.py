import pytest

from groove.db.manager import database_manager
from groove.shell import interactive_shell
from unittest.mock import MagicMock


@pytest.fixture
def cmd_prompt(in_memory_engine, db):
    with database_manager() as manager:
        manager._session = db
        yield interactive_shell.CommandPrompt(manager)


def response_factory(responses):
    return MagicMock(side_effect=responses + ([''] * 10))


@pytest.mark.parametrize('inputs, expected', [
    (['stats'], 'Database contains 4 playlists'),  # match the db fixture
])
def test_stats(monkeypatch, capsys, cmd_prompt, inputs, expected):
    monkeypatch.setattr('groove.shell.base.prompt', response_factory(inputs))
    cmd_prompt.start()
    output = capsys.readouterr()
    assert expected in output.out


@pytest.mark.parametrize('inputs, expected', [
    (['quit'], SystemExit),
])
def test_quit(monkeypatch, capsys, cmd_prompt, inputs, expected):
    monkeypatch.setattr('groove.shell.base.prompt', response_factory(inputs))
    with pytest.raises(expected):
        cmd_prompt.start()


def test_browse(monkeypatch, capsys, cmd_prompt):
    monkeypatch.setattr('groove.shell.base.prompt', response_factory(['browse']))
    cmd_prompt.start()
    output = capsys.readouterr()
    assert 'Displaying 4 playlists' in output.out
    assert 'playlist one' in output.out
    assert 'the first one' in output.out
    assert 'playlist-one' in output.out
    assert 'the second one' in output.out
    assert 'the threerd one' in output.out
    assert 'empty playlist' in output.out


@pytest.mark.parametrize('inputs, expected', [
    ('help', ['Available Commands', ' help ', ' stats ', ' browse ']),
    ('help browse', ['Help for browse']),
])
def test_help(monkeypatch, capsys, cmd_prompt, inputs, expected):
    monkeypatch.setattr('groove.shell.base.prompt', response_factory([inputs]))
    cmd_prompt.start()
    output = capsys.readouterr()
    for txt in expected:
        assert txt in output.out


@pytest.mark.parametrize('inputs, expected', [
    ('load A New Playlist', 'a-new-playlist'),
    ('new playlist', 'new-playlist'),
    ('load', '')
])
def test_load(monkeypatch, caplog, cmd_prompt, inputs, expected):
    monkeypatch.setattr('groove.shell.base.prompt', response_factory([inputs]))
    cmd_prompt.start()
    assert expected in caplog.text

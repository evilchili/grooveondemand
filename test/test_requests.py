from groove.webserver import requests


def test_signing():
    signed = requests.encode(['foo', 'bar'], uri='fnord')
    assert requests.verify(signed, signed)


def test_signing_wrong_secret_key(env):
    signed = requests.encode(['foo', 'bar'], uri='fnord')
    env['SECRET_KEY'] = 'wrong key'
    invalid = requests.encode(['foo', 'bar'], uri='fnord')
    assert not requests.verify(invalid, signed)


def test_signing_wrong_uri(env):
    signed = requests.encode(['foo', 'bar'], uri='fnord')
    invalid = requests.encode(['foo', 'bar'], uri='a bad guess')
    assert not requests.verify(invalid, signed)

import pytest


@pytest.fixture(scope='session')
def valid_credentials():
    return (os.environ.get('USERNAME'), os.environ.get('PASSWORD'))

from boddle import boddle
from groove import ondemand
import os


def test_ondemand_server():
    with boddle():
        assert ondemand.index() == 'Groovy.'


def test_ondemand_auth():
    with boddle(auth=(os.environ.get('USERNAME'), os.environ.get('PASSWORD'))):
        assert ondemand.admin() == 'Authenticated. Groovy.'

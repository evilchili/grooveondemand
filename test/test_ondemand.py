import os
import sys

import atheris
from boddle import boddle

from groove import ondemand


def test_server():
    with boddle():
        assert ondemand.index() == 'Groovy.'


def test_auth_with_valid_credentials():
    with boddle(auth=(os.environ.get('USERNAME'), os.environ.get('PASSWORD'))):
        assert ondemand.admin() == 'Authenticated. Groovy.'


def test_auth_random_input():

    def auth(fuzzed_input):
        with boddle(auth=(fuzzed_input, fuzzed_input)):
            result = ondemand.admin()
            assert result.body == 'Access denied'

    atheris.Setup([sys.argv[0], "-atheris_runs=100000"], auth)
    try:
        atheris.Fuzz()
    except SystemExit:
        pass

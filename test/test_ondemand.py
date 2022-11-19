from boddle import boddle
from groove import ondemand


def test_ondemand_server():
    with boddle():
        assert ondemand.index() == 'Groovy.'

import logging
import os


def is_authenticated(username, password):
    logging.debug(f"Authentication attempt for {username}, {password}")
    return (username == os.environ.get('USERNAME') and password == os.environ.get('PASSWORD'))

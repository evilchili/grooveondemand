import logging
import os


def is_authenticated(username: str, password: str) -> bool:
    """
    Returns True if the supplied username/password matches the environment.
    """
    logging.debug(f"Authentication attempt for {username}, {password}")
    return (username == os.environ.get('USERNAME') and password == os.environ.get('PASSWORD'))

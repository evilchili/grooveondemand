from hashlib import blake2b
from hmac import compare_digest
from typing import List
import os


def encode(args: List, uri: str) -> str:
    """
    Encode a request and cryptographically sign it. This serves two purposes:
    First, it enables the handler that receives the request to verify that the
    request was meant for it, preventing various routing and relay-induced bugs.
    Second, it ensures the request wasn't corrutped or tampered with during
    transmission.

    Args:
        args (List): a list of parameters to pass along with the request.
        uri (String): the URI of the intended handler for the request.

    Returns:
        String: A cryptographically signed request.
    """
    return sign(uri + '\0' + '\0'.join(args))


def sign(request):
    """
    Sign a request with a cryptographic hash.  Returns the hex digest.
    """
    h = blake2b(digest_size=16, key=bytes(os.environ['SECRET_KEY'].encode()))
    h.update(request.encode())
    return h.hexdigest()


def verify(request, digest):
    return compare_digest(request, digest)


def url():
    return f"http://{os.environ['HOST']}:{os.environ['PORT']}"

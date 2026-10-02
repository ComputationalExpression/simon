from _typeshed import Incomplete

decompress: Incomplete
compress: Incomplete
crc32: Incomplete

class Adler32:
    def __init__(self, data: bytes = b'') -> None: ...
    def update(self, data: bytes) -> None: ...
    def digest(self) -> int: ...

adler32: Incomplete

from _typeshed import Incomplete
from typing import Any

INT8: int
INT16: int
INT32: int
INT64: int
UINT8: int
UINT16: int
UINT32: int
UINT64: int
FLOAT32: int
FLOAT64: int
VOID: int
PTR: int
ARRAY: int
LITTLE_ENDIAN: int
BIG_ENDIAN: int
NATIVE: int
sizeof: Incomplete
addressof: Incomplete
bytes_at: Incomplete
bytearray_at: Incomplete

class struct:
    def __init__(self, addr: int, descriptor: Any, layout_type: int = ...) -> None: ...

class union(struct): ...

class bytearray_:
    def __init__(self, data: Any) -> None: ...

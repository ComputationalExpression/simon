from _typeshed import Incomplete
from typing import Any

stdin: Incomplete
stdout: Incomplete
stderr: Incomplete
argv: list[str]
path: list[str]
modules: dict[str, Any]
platform: str
version: str
version_info: Incomplete
implementation: Incomplete
byteorder: str
maxsize: int
exit: Incomplete
print_exception: Incomplete

class _ExcInfo:
    exc: Incomplete
    def __init__(self, exc: Any) -> None: ...
    def __enter__(self) -> Any: ...
    def __exit__(self, *args: Any) -> bool: ...

def exc_info() -> Any: ...

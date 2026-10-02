from _typeshed import Incomplete
from collections.abc import Callable as Callable
from typing import Any

def namedtuple(name: str, fields: Any) -> Callable[..., Any]: ...

OrderedDict: Incomplete
deque: Incomplete

class defaultdict(dict[Any, Any]):
    default_factory: Incomplete
    def __init__(self, default_factory: Any = None, *args: Any, **kwargs: Any) -> None: ...
    def __missing__(self, key: Any) -> Any: ...

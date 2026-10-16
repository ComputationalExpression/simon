"""Structure checks for Lab 5: Simon Memory Game.

These read `src/main.py` as Python, not as text, so the words in the story
and in comments do not count. Only real statements do. Each assertion message
says what was found and what was expected.
"""

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "src" / "main.py"


def tree():
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def nodes(kind):
    return [n for n in ast.walk(tree()) if isinstance(n, kind)]


def calls_to(name):
    """Calls written `name(...)` or `something.name(...)`."""
    found = []
    for call in nodes(ast.Call):
        func = call.func
        if isinstance(func, ast.Attribute) and func.attr == name:
            found.append(call)
        elif isinstance(func, ast.Name) and func.id == name:
            found.append(call)
    return found


def test_randint_is_called():
    assert calls_to("randint") or calls_to("randrange"), (
        "found no call to random.randint(...) or random.randrange(...): Simon picks each light at random"
    )


def test_append_is_called():
    assert calls_to("append"), "found no call to .append(...): sequence and answer both grow one item at a time"


def test_a_while_loop_reads_the_button():
    found = []
    for loop in nodes(ast.While):
        for call in ast.walk(loop.test):
            if isinstance(call, ast.Call) and (
                (isinstance(call.func, ast.Attribute) and call.func.attr == "value")
                or isinstance(call.func, ast.Name)
            ):
                found.append(loop)
    assert found, "found no while loop whose condition reads the button: `while button.value() == 1:` moves the light along until a press"


def test_a_for_loop_over_a_list():
    found = [loop for loop in nodes(ast.For) if isinstance(loop.iter, ast.Name)]
    assert found, "found no for loop over a list: `for position in sequence:` plays Simon's sequence"


def test_two_lists_compared_by_position():
    found = [
        compare for compare in nodes(ast.Compare)
        if any(isinstance(side, ast.Subscript) for side in [compare.left] + compare.comparators)
    ]
    assert found, "found no comparison of one item of a list, like answer[position] == sequence[position]: the score checks one position at a time"

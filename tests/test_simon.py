"""Automated checks for Lab 5: Simon Memory Game.

Every check reads the Simon log at the end of the run, or looks at which
lights came on, never the narrative lines, so the story is the student's to
word. Log values are matched loosely: any amount of whitespace, any letter
case, and the colon is optional, so `print("Correct steps:", correct)`,
`print("Correct steps: " + str(correct))`, and an f-string all read the same.

Simon's sequence is chosen by each check rather than at random:
random.randint hands back the positions the check lists, in order. The button
is pressed by a pretend player who watches the lights. Every time a light
comes on and the program then reads the button, the player decides: if that
is the light they want for this step, they press, and the press answers the
step. A slow player lets the light they want go past once before pressing.

The lights are told apart by the order each `Pin(...)` was made in, numbered
1, 2, 3, and the button is the Pin made with `Pin.IN`. A student may wire more
than three lights; the checks count the lights the program made.

When a check fails, the assertion message says what came out wrong, what was
expected, and the sequence and presses used. gatorgrade does not show that
message itself; it prints the pytest command to run.
"""

import re
from unittest.mock import patch

import mockro
from machine import Pin

import main as program

# More button reads than this without the player answering means the program is
# stuck waiting. Every run here needs a few dozen at most.
MOST_READS = 5000


class Board:
    """The lights and the button, with a pretend player at the button.

    `wanted` lists the position the player presses for at each step, counting
    from 0 like the list does.
    """

    def __init__(self, wanted, slow=False):
        self.wanted = list(wanted)
        self.slow = slow
        self.step = 0
        self.let_pass = False
        self.fresh = False
        self.lit = []
        self.first_read = None
        self.reads = 0

    def who(self, pin):
        """1, 2, 3 for the lights in the order they were made, "button", or None."""
        lights = 0
        for args, _ in mockro.get_recorder().calls("machine.Pin.init"):
            if len(args) < 4:
                continue
            if args[3] == Pin.IN:
                if args[0] is pin:
                    return "button"
            elif isinstance(args[2], int):
                lights += 1
                if args[0] is pin:
                    return lights
        return None

    def light_on(self, light):
        self.lit.append(light)
        self.fresh = True

    def on(self, pin, *rest):
        light = self.who(pin)
        if isinstance(light, int):
            self.light_on(light)

    def off(self, pin, *rest):
        return None

    def value(self, pin, *rest):
        # mockro passes the Pin twice, then the argument: (pin, pin, x)
        x = rest[-1] if rest and rest[-1] is not pin else None
        part = self.who(pin)
        if part == "button" and x is None:
            return self.read()
        if isinstance(part, int) and x:
            self.light_on(part)
        return 0

    def read(self):
        """What the button reads now: 0 when the player presses, 1 otherwise."""
        self.reads += 1
        if self.first_read is None:
            self.first_read = len(self.lit)
        if self.reads > MOST_READS:
            raise AssertionError(
                f"the button was read {MOST_READS} times after the player had answered "
                f"{self.step} of {len(self.wanted)} steps, so the program was stuck waiting"
            )
        if self.step < len(self.wanted) and self.fresh and self.lit[-1] == self.wanted[self.step] + 1:
            self.fresh = False
            if self.slow and not self.let_pass:
                self.let_pass = True
                return 1
            self.step += 1
            self.let_pass = False
            return 0
        return 1

    def watched(self):
        """The lights that came on before the button was first read."""
        return self.lit if self.first_read is None else self.lit[:self.first_read]


def numbers(positions):
    return ", ".join(str(position + 1) for position in positions)


def describe(sequence, presses, slow=False):
    who = "a slow player" if slow else "a player"
    return f"Simon's lights {numbers(sequence)}; {who} pressing on lights {numbers(presses)}"


def run(capsys, sequence, presses=None, slow=False, name="JJ"):
    """Run main() once. Returns what it printed, the board, and the randint calls."""
    presses = sequence if presses is None else presses
    typed = [name, str(len(sequence))]
    picks = list(sequence)
    calls = []

    def randint(low, high):
        calls.append((low, high))
        if len(calls) > len(picks):
            raise AssertionError(
                f"random.randint was called {len(calls)} times for a sequence of {len(picks)}: "
                f"call it once for every light Simon shows"
            )
        return picks[len(calls) - 1]

    board = Board(presses, slow)
    mockro.get_recorder().clear()
    stubs = [patch("random.randint", side_effect=randint)]
    if hasattr(program, "randint"):
        stubs.append(patch.object(program, "randint", side_effect=randint))
    try:
        with patch("builtins.input", side_effect=typed), patch("time.sleep", return_value=None), \
                mockro.override(machine_Pin_value=board.value, machine_Pin_on=board.on,
                                machine_Pin_off=board.off):
            for stub in stubs:
                stub.start()
            try:
                program.main()
            finally:
                for stub in stubs:
                    stub.stop()
    except AssertionError:
        raise
    except Exception as exc:
        raise AssertionError(
            f"the program stopped with {type(exc).__name__}: {exc} ({describe(sequence, presses, slow)})"
        ) from None
    out, err = capsys.readouterr()
    assert err == "", "the program wrote to the error stream:\n" + err
    return out, board, calls


def log_value(out, label):
    """Return the value printed after `label` in the Simon log, normalized.

    Only the part of the output from `SIMON LOG` onward is searched. Whitespace
    is collapsed inside the label and the value, case is folded to upper, a
    trailing period is dropped, and the colon after the label is optional.
    Returns None when the log, or the label, was never printed.
    """
    start = out.upper().find("SIMON LOG")
    if start < 0:
        return None
    words = r"\s+".join(re.escape(word) for word in label.split())
    match = re.search(rf"^\s*{words}\s*:?\s*([^\n]*)", out[start:], re.IGNORECASE | re.MULTILINE)
    if match is None:
        return None
    return " ".join(match.group(1).split()).upper().rstrip(".! ")


def expect(out, label, want, context):
    if "SIMON LOG" not in out.upper():
        raise AssertionError(f'no "SIMON LOG" line was printed ({context})')
    got = log_value(out, label)
    if got is None:
        raise AssertionError(f'no "{label}" line was printed after SIMON LOG ({context})')
    assert got == str(want).upper(), f'the "{label}" line said {got}, expected {want} ({context})'


def light_count(capsys):
    """How many external lights the program makes, from one short run."""
    run(capsys, [0])
    return len({id(args[0]) for args, _ in mockro.get_recorder().calls("machine.Pin.init")
                if len(args) > 3 and isinstance(args[2], int) and args[3] != Pin.IN})


def test_program_runs_and_log_names_you(capsys):
    lights = light_count(capsys)
    assert lights >= 3, f"the program made {lights} lights, expected at least 3: leds = [Pin(15, Pin.OUT), Pin(14, Pin.OUT), Pin(13, Pin.OUT)]"
    out, _, _ = run(capsys, [0])
    context = describe([0], [0])
    # The starter prints its own framing text either way, so the user's name
    # in the log is what shows that Stage One and the log are done.
    expect(out, "SIMON LOG", "JJ", context)
    expect(out, "Lights", lights, context)


def test_randint_picks_a_position(capsys):
    lights = light_count(capsys)
    sequence = [2, 0, 1, 1]
    out, _, calls = run(capsys, sequence)
    assert len(calls) == len(sequence), (
        f"random.randint was called {len(calls)} times for a sequence of {len(sequence)}: "
        f"call it once for every light Simon shows"
    )
    wrong = sorted({call for call in calls if call != (0, lights - 1)})
    assert not wrong, (
        f"random.randint was called with {wrong[0]}, expected (0, {lights - 1}): positions start at 0, "
        f"and randint includes both ends, so the last position is len(leds) - 1"
    )
    expect(out, "Sequence length", 4, describe(sequence, sequence))


def test_watch_plays_the_sequence_in_order(capsys):
    sequence = [2, 0, 1, 1]
    _, board, _ = run(capsys, sequence)
    shown = board.watched()
    window = [position + 1 for position in sequence]
    found = any(shown[start:start + len(window)] == window for start in range(len(shown)))
    assert found, (
        f"Simon's sequence was lights {numbers(sequence)}, but before the button was first read the "
        f"lights came on in this order: {shown}. Loop over `sequence` and light leds[position]"
    )


def test_a_perfect_answer_scores_every_step(capsys):
    for sequence in ([2, 0, 1, 1], [1, 2]):
        out, _, _ = run(capsys, sequence)
        context = describe(sequence, sequence)
        expect(out, "Correct steps", len(sequence), context)
        expect(out, "Result", "PERFECT", context)


def test_a_wrong_press_is_scored_by_position(capsys):
    sequence = [2, 0, 1, 1]
    for presses, want in (([2, 1, 1, 1], 3), ([0, 0, 0, 0], 1)):
        out, _, _ = run(capsys, sequence, presses)
        context = describe(sequence, presses)
        expect(out, "Correct steps", want, context)
        expect(out, "Result", "TRY AGAIN", context)


def test_the_light_goes_round_again(capsys):
    # The slow player lets the first light pass, so the light has to come back
    # round from the last one to the first before it can be chosen.
    sequence = [0, 2, 1]
    out, _, _ = run(capsys, sequence, slow=True)
    context = describe(sequence, sequence, slow=True)
    expect(out, "Correct steps", 3, context)
    expect(out, "Result", "PERFECT", context)

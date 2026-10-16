"""Automated checks for Lab 5: Simon Memory Game.

Every check reads the Simon log at the end of the run, or looks at which
lights came on, never the narrative lines, so the story is the student's to
word. Log values are matched loosely: any amount of whitespace, any letter
case, and the colon is optional, so `print("Correct steps:", correct)`,
`print("Correct steps: " + str(correct))`, and an f-string all read the same.
Words after the value are allowed, so "Correct steps: 3 of 4" reads as 3.

Simon's sequence is chosen by each check rather than at random:
random.randint returns the positions the check lists, in order, and so does
random.randrange. Answers after the two the checks type are blank, so an
extra "Press Enter" prompt is fine.

The button is pressed by a pretend player who watches the lights. Every time
a light comes on and the program then reads the button, the player decides:
if that is the light they want for this step, they press, and they hold the
button down until a light goes off or on, so the program may read it more
than once. A slow player lets the light they want go past once before
pressing. A program that waits for a press while no light is on, such as
"press the button to start", gets one after a two-second wait.

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

# More button reads than this means the program is stuck waiting. Every run
# here needs a few thousand at most, even polling with no sleep.
MOST_READS = 20000
# A press is held at most this long, in seconds of time.sleep, or this many
# reads, before the player lets go without a light changing.
HOLD_SECONDS = 1.0
HOLD_READS = 1000
# With no light on to choose, the player presses after this long, or after
# this many reads, as if asked to press to start.
IDLE_SECONDS = 2.0
IDLE_READS = 2000


class Board:
    """The lights and the button, with a pretend player at the button.

    `wanted` lists the position the player presses for at each step, counting
    from 0 like the list does. `clock` adds up every time.sleep.
    """

    def __init__(self, wanted, slow=False):
        self.wanted = list(wanted)
        self.slow = slow
        self.step = 0
        self.let_pass = False
        self.fresh = False
        self.lit = []
        self.first_answer = None
        self.reads = 0
        self.clock = 0.0
        self.held = False
        self.since = 0.0
        self.since_reads = 0
        self.on_now = set()
        self.roles = {}

    def sleep(self, seconds=0, *rest):
        self.clock += seconds

    def changed(self):
        """A light went on or off: the player lets go, and starts watching again."""
        self.held = False
        self.since = self.clock
        self.since_reads = self.reads

    def who(self, pin):
        """1, 2, 3 for the lights in the order they were made, "button", or None."""
        if id(pin) not in self.roles:
            self.roles[id(pin)] = self.find(pin)
        return self.roles[id(pin)]

    def find(self, pin):
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
        self.on_now.add(light)
        self.fresh = True
        self.changed()

    def on(self, pin, *rest):
        light = self.who(pin)
        if isinstance(light, int):
            self.light_on(light)

    def off(self, pin, *rest):
        light = self.who(pin)
        if isinstance(light, int):
            self.on_now.discard(light)
            self.changed()

    def value(self, pin, *rest):
        # mockro passes the Pin twice, then the argument: (pin, pin, x)
        x = rest[-1] if rest and rest[-1] is not pin else None
        part = self.who(pin)
        if part == "button" and x is None:
            return self.read()
        if isinstance(part, int):
            if x:
                self.light_on(part)
            elif x is not None:
                self.on_now.discard(part)
                self.changed()
        return 0

    def read(self):
        """What the button reads now: 0 while the player presses, 1 otherwise."""
        self.reads += 1
        if self.reads > MOST_READS:
            raise AssertionError(
                f"the button was read {MOST_READS} times after the player had answered "
                f"{self.step} of {len(self.wanted)} steps, so the program was stuck waiting"
            )
        waited = self.clock - self.since
        read_since = self.reads - self.since_reads
        if self.held:
            if waited < HOLD_SECONDS and read_since < HOLD_READS:
                return 0
            self.changed()
        if self.step < len(self.wanted) and self.fresh and self.on_now == {self.wanted[self.step] + 1}:
            self.fresh = False
            if self.slow and not self.let_pass:
                self.let_pass = True
                return 1
            if self.first_answer is None:
                self.first_answer = len(self.lit)
            self.step += 1
            self.let_pass = False
            return self.press()
        if not self.on_now and (waited >= IDLE_SECONDS or read_since >= IDLE_READS):
            return self.press()
        return 1

    def press(self):
        self.held = True
        self.since = self.clock
        self.since_reads = self.reads
        return 0

    def watched(self):
        """The lights that came on before the player answered the first step."""
        return self.lit if self.first_answer is None else self.lit[:self.first_answer]


def numbers(positions):
    return ", ".join(str(position + 1) for position in positions)


def describe(sequence, presses, slow=False):
    who = "a slow player" if slow else "a player"
    return f"Simon's lights {numbers(sequence)}; {who} pressing on lights {numbers(presses)}"


def run(capsys, sequence, presses=None, slow=False, name="JJ"):
    """Run main() once. Returns what it printed, the board, and the random calls.

    Each random call is kept as (lowest, highest) it could pick, so
    randint(0, 2), randrange(3) and randrange(0, 3) are all (0, 2).
    """
    presses = sequence if presses is None else presses
    typed = [name, str(len(sequence))]
    picks = list(sequence)
    calls = []

    def typing(prompt=""):
        return typed.pop(0) if typed else ""

    def pick(low, high):
        """The next scripted position, counted from `low` when it fits."""
        calls.append((low, high))
        if len(calls) > len(picks):
            raise AssertionError(
                f"random.randint was called {len(calls)} times for a sequence of {len(picks)}: "
                f"call it once for every light Simon shows"
            )
        position = picks[len(calls) - 1]
        return low + position if low + position <= high else position

    def randint(low, high):
        return pick(low, high)

    def randrange(start, stop=None, *rest):
        if stop is None:
            start, stop = 0, start
        return pick(start, stop - 1)

    board = Board(presses, slow)
    mockro.get_recorder().clear()
    stubs = [patch("random.randint", side_effect=randint),
             patch("random.randrange", side_effect=randrange),
             patch("time.sleep", side_effect=board.sleep)]
    for name_in_program, fake in (("randint", randint), ("randrange", randrange), ("sleep", board.sleep)):
        if hasattr(program, name_in_program):
            stubs.append(patch.object(program, name_in_program, side_effect=fake))
    try:
        with patch("builtins.input", side_effect=typing), \
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

    Only the part of the output from the last line that starts with `SIMON LOG`
    onward is searched, so the story may mention the log first. Whitespace
    is collapsed inside the label and the value, case is folded to upper, a
    trailing period is dropped, and the colon after the label is optional.
    Returns None when the log, or the label, was never printed.
    """
    starts = [line.start() for line in re.finditer(r"^\s*SIMON\s+LOG", out, re.IGNORECASE | re.MULTILINE)]
    if not starts:
        return None
    start = starts[-1]
    words = r"\s+".join(re.escape(word) for word in label.split())
    match = re.search(rf"^\s*{words}\s*:?\s*([^\n]*)", out[start:], re.IGNORECASE | re.MULTILINE)
    if match is None:
        return None
    return " ".join(match.group(1).split()).upper().rstrip(".! ")


def expect(out, label, want, context):
    if log_value(out, "SIMON LOG") is None:
        raise AssertionError(f'no "SIMON LOG" line was printed ({context})')
    got = log_value(out, label)
    if got is None:
        raise AssertionError(f'no "{label}" line was printed after SIMON LOG ({context})')
    # The value comes first; words after it, like "of 4", are allowed
    assert re.match(rf"{re.escape(str(want).upper())}(?![A-Z0-9])", got), f'the "{label}" line said {got}, expected {want} ({context})'


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
        f"random.randint could pick from {wrong[0][0]} to {wrong[0][1]}, expected 0 to {lights - 1}: positions "
        f"start at 0, and randint includes both ends, so the last position is len(leds) - 1"
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

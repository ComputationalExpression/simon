"""Simon Memory Game.

CMPSC 100: Computational Expression, Lab 5

Simon lights a sequence, and you play it back with one button. On your turn
the lights take turns, one at a time, and you hold the button down while the
light you want is on. Simon's sequence and your answer are two lists, and the
score compares them position by position.

Every message this program prints is yours to word. The automated checks read
only the Simon log at the end, and which lights came on.

Author: TODO
"""

from machine import Pin
import random
import time


def main():
    # The three lights from Lab 4, in the same order, and the button. PULL_UP
    # holds the button's pin at 1 until a press connects it to ground, so a
    # press reads 0
    leds = [Pin(15, Pin.OUT), Pin(14, Pin.OUT), Pin(13, Pin.OUT)]
    button = Pin(16, Pin.IN, Pin.PULL_UP)

    print("=" * 50)
    print("SIMON MEMORY GAME")
    print("=" * 50)

    # ===== Stage One: Simon's Sequence =====

    # TODO 1: ask the user's name, save it to a variable called `name`

    # TODO 2: ask how many lights Simon should show (1-8), save it to a
    # variable called `length`, and convert it to an int

    # TODO 3: set a variable called `sequence` to an empty list, then loop
    # over range(length). On every trip, append
    # random.randint(0, len(leds) - 1) to `sequence`

    # ===== Stage Two: Watch =====

    print()

    # TODO 4: print a message that uses `name`, then time.sleep(1). Play the
    # sequence with a for loop over `sequence`: on every trip,
    # leds[position].on(), time.sleep(0.6), leds[position].off(),
    # time.sleep(0.3)

    # ===== Stage Three: Your Turn =====

    # TODO 5: set a variable called `answer` to an empty list, then loop over
    # range(length). Each trip answers one step:
    #   - set `lit` to 0, then leds[lit].on() and time.sleep(0.5)
    #   - while button.value() is 1: leds[lit].off(), add 1 to `lit`, set
    #     `lit` back to 0 if it equals len(leds), then leds[lit].on() and
    #     time.sleep(0.5)
    #   - after the while loop: leds[lit].off(), append `lit` to `answer`,
    #     print which light was chosen, and time.sleep(0.5)

    # ===== Stage Four: The Score =====

    # TODO 6: set `correct` to 0, then loop over range(length) and add 1 to
    # `correct` whenever answer[position] equals sequence[position]

    # TODO 7: if `correct` equals `length`, set `result` to "PERFECT" and
    # flash every light together three times; else set `result` to
    # "TRY AGAIN"

    print()
    print("=" * 50)

    # TODO 8: print the Simon log, one line each, in this order:
    # "SIMON LOG: {name}", then a line of 50 "=" characters, then
    # "Lights: {len(leds)}", "Sequence length: {len(sequence)}",
    # "Correct steps: {correct}", and "Result: {result}"
    # Print each value any way you like: commas, + with str(), or an f-string


if __name__ == "__main__":
    main()

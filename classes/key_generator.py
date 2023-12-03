# Standard library imports
from time import sleep
from numpy import random
from threading import Timer

# Third party imports
from pynput.keyboard import Controller

# KeyMaster imports
from utils.config import BANNED_KEYS, KEYBOARD_CHARS, MIN_DELAY, SIM_SPEED_MULTIPLE, SIM_DELAY_MEAN, SIM_DELAY_STD_DEV, SIM_MAX_SPEED, SIM_MAX_WORDS, SHIFT_SPEED, SIM_MAX_DURATION
from utils.config import STOP_KEY, STOP_CODE, APOSTROPHE, SPECIAL_KEYS, DEFAULT_DISABLE_SIMULATION, SHIFTED_CHARS, SHOW_SHIFT_INSERTIONS
from utils.config import ROUND_DIGITS, DEFAULT_ALLOW_NEWLINES, DEFAULT_ALLOW_UNICODE
from utils.validation import Keystroke, Key, KeystrokeList, unwrap_key

import logging
logging.basicConfig(encoding='utf-8', level=logging.INFO)


class KeyGenerator:
    """
    A class used to simulate keystrokes and log them.

    Attributes:
        speed_multiplier (float or int): The speed multiplier.
        delay_mean (float): The mean delay between keystrokes.
        delay_standard_deviation (float): The standard deviation of the delay between keystrokes.
        max_words (int): The maximum number of words to simulate.
        min_delay (float): The minimum delay between keystrokes.
        special_keys (dict): A dictionary of special keys and their corresponding keys.
        whitespace_dict (dict): A dictionary of encoded characters and their corresponding strings.
        disable (bool): Whether or not the simulation is disabled.
        max_duration (float): The maximum duration of the simulation.
    """

    def __init__(
            self,
            disable: bool = DEFAULT_DISABLE_SIMULATION,
            max_duration: int | float = SIM_MAX_DURATION,
            max_words: int = SIM_MAX_WORDS,
            speed_multiplier: int | float = SIM_SPEED_MULTIPLE,
            allow_newlines: bool = DEFAULT_ALLOW_NEWLINES,
            allow_unicode: bool = DEFAULT_ALLOW_UNICODE,
            round_digits: int = ROUND_DIGITS,
            banned_keys: list[str] = BANNED_KEYS) -> None:
        """
        Initialize the KeyGenerator with the given parameters.
        """
        self.disable = disable  # Client facing
        self.max_duration = float(max_duration)  # Client facing
        self.round_digits = round_digits  # Client facing
        self.max_words = max_words  # Client facing
        self.speed_multiplier = float(speed_multiplier)  # Client facing

        self.allow_newlines = allow_newlines
        self.allow_unicode = allow_unicode
        self.simulation_timer: Timer | None = None
        self.stop = False
        self.whitespace_dict = {
            ' ': str(Key.space),
            '\t': str(Key.tab),
            '\n': str(Key.enter)
        }
        if not self.allow_newlines:
            self.whitespace_dict.pop('\n')
        self.banned_keys = banned_keys

    def set_speed(self, speed: float | int) -> None:
        """Client facing.
        Set the speed multiplier.

        Args:
            speed (float): The speed multiplier.
        """
        if speed < 0:
            raise ValueError("Speed multiplier must be greater than 0.")
        if speed > SIM_MAX_SPEED:
            logging.error(
                f"Invalid speed multiplier: {speed}. Setting to {SIM_MAX_SPEED}")
            self.speed_multiplier = SIM_MAX_SPEED
        self.speed_multiplier = float(speed)

    def calculate_delay(self, speed_multiple: float | int | None) -> float:
        """Not client facing.
        Get a normally distributed delay between keystrokes.

        Args:
            speed_multiple: The speed multiplier.

        Returns:
            float: The delay between keystrokes.
        """
        # Ensure speed_by_multiple > 0
        if speed_multiple is None:
            speed_multiple = self.speed_multiplier

        speed_multiple = float(speed_multiple)
        if speed_multiple <= 0:
            # ERROR
            logging.error(
                f"Invalid speed multiplier: {speed_multiple}. Setting to 1")
            speed_multiple = 1
        delay = random.normal(
            SIM_DELAY_MEAN / (speed_multiple),
            SIM_DELAY_STD_DEV / speed_multiple)
        if delay < MIN_DELAY:
            # print(f"Delay too low: {delay}")
            delay = MIN_DELAY + delay / 10
        return delay

    def generate_keystrokes_from_string(
            self, input_string: str) -> KeystrokeList:
        """Client facing.
        Generate valid Keystrokes from a string. Output object can be simulated.

        Returns:
            KeystrokeList: A list of keystrokes.
        """
        # The rest of the code from the simulate_keystrokes function goes here.
        keystrokes = KeystrokeList()
        if not input_string:
            print("No input string provided.")
            return keystrokes
        word_count = 0

        string_length = len(input_string)
        for i in range(string_length):
            if word_count == self.max_words:
                logging.info(f"Reached max words: {self.max_words}")
                break
            char = input_string[i]
            keystroke = self.generate_keystroke(char)
            if keystroke is None:
                continue
            if char == ' ':
                word_count += 1

            if len(keystrokes) == 0:
                last_key = None
            else:
                last_key = keystrokes[-1].key
            # Lambda function to check if a key is eligible to have shift
            # before it

            def shift_eligible(k): return (
                k is None or k == ' ') or (
                k not in SHIFTED_CHARS and not k.isupper())

            # Check if a shift key needs to be added
            if shift_eligible(
                    last_key):  # isn't last key wrapped in apostrophes?
                if char.isupper() or (char in SHIFTED_CHARS):
                    if SHOW_SHIFT_INSERTIONS:
                        logging.info(f"Inserting shift before key {i}: {char}")
                    # Add a shift keypress
                    if keystrokes.is_empty():
                        time = None
                    else:
                        time = SHIFT_SPEED
                    key = str(Key.shift)
                    keystrokes.append(Keystroke(key, time))
            if keystrokes.is_empty():
                keystroke.time = None
            keystrokes.append(keystroke)
            # Should I stop generation at stop key too?
            if char == STOP_KEY:
                logging.warning(
                    'STOP key found. Halting keystroke generation.')
                break
        return keystrokes

    def wrap_character(self, char: str) -> str:
        """Not client facing.
        Wrap a character in single quotes.
        """
        return APOSTROPHE + char + APOSTROPHE

    def generate_keystroke(self, char: str) -> Keystroke | None:
        """Client facing.
        Generate a `Keystroke` from a character (`str`).
        """
        if len(char) != 1:
            logging.error(f"generate_keystroke: Character length is not 1: {char}")
            return None
        key_string = char
        if char in self.whitespace_dict:
            key_string = (self.whitespace_dict[char])
        elif char.isprintable():
            # Add '' around the character
            if char == STOP_KEY:
                key_string = STOP_CODE
            else:
                if not self.allow_unicode and char not in KEYBOARD_CHARS:
                    # logging.error(f"generate_keystroke: Unicode character not allowed: {char} -> {ord(char)}")
                    return None
                key_string = APOSTROPHE + char + APOSTROPHE
        else:
            logging.error(
                f"generate_keystroke: Non-printable character: {char} -> {ord(char)}")
            return None

        delay1 = self.calculate_delay(1)
        delay2 = self.calculate_delay(1.5)
        delay = round(delay1 + delay2, self.round_digits)
        return Keystroke(key_string, delay)

    def stop_simulation(self) -> None:
        """Not client facing.
        Stop the simulation.
        """
        if self.stop:
            return
        self.stop = True
        if self.simulation_timer:
            self.simulation_timer.cancel()

    def simulate_keystrokes(self, keystrokes: KeystrokeList) -> None:
        """Client facing.
        Function to simulate the given keystrokes.

        Args:
            keystrokes (KeystrokeList, optional): The list of keystrokes to simulate.
        """
        if self.disable:
            logging.error("Simulation disabled.")
            return
        if keystrokes.is_empty():
            logging.error("No keystrokes found.")
            return

        none_count = 0
        self.stop = False
        # Initialize the keyboard controller
        keyboard = Controller()
        self.simulation_timer = Timer(
            self.max_duration,
            lambda: self.stop_simulation())
        self.simulation_timer.start()
        for keystroke in keystrokes:
            if self.stop:
                logging.info(
                    f'Duration {self.max_duration}s elapsed. Stopping simulation.')
                break
            if not keystroke.valid:
                logging.error(
                    f"simulate_keystrokes: Invalid key: {keystroke.key}")
                continue

            key = keystroke.key
            if key == STOP_CODE:
                key = STOP_KEY
            time = keystroke.time
            if time is None:
                none_count += 1
                if none_count > 1:
                    logging.error(
                        'Critical error: None value marks first character. Only use once')
                    break
                # What should this time diff be?
                delay = 0.0
            else:
                delay = time
                # If time difference is greater than 3 seconds, set diff to 3.x
                # seconds with decimal coming from delay
                if self.speed_multiplier > 0:
                    delay = delay / self.speed_multiplier
                if delay > 3:
                    delay = 3 + (delay / 1000)
            try:
                if delay > 0:
                    # Wait for the time difference between keystrokes
                    sleep(delay)
                if key in SPECIAL_KEYS:
                    keyboard.tap(SPECIAL_KEYS[key])
                else:
                    # Decode the character
                    key = unwrap_key(key)
                    try:
                        keyboard.tap(key)
                    except Exception as e:
                        logging.error(
                            f"ERROR! Decoded key was not a character: {key}")
                        continue

                if key == STOP_KEY:
                    logging.warning('STOP key found. Stopping simulation.')
                    break
            except Exception as e:
                logging.critical(f"An error occurred: {e}")
                break
        self.stop_simulation()

    def simulate_string(self, string: str) -> KeystrokeList | None:
        """Client facing.
        Simulate the given string.

        Args:
            string (str): The string to simulate.
        """
        keystrokes = self.generate_keystrokes_from_string(string)
        if keystrokes.is_empty():
            logging.error("Given input was not simulated.")
            return None
        self.simulate_keystrokes(keystrokes)
        return keystrokes

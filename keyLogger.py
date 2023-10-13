from pynput.keyboard import Key, KeyCode, Listener, Controller
from time import time, sleep
import json
import uuid
from os import path
from config import ROOT, ABSOLUTE_REG_FILEPATH, MAX_WORDS, SPEEDHACK, SPEED_MULTIPLE, STOP_KEY, SPECIAL_KEYS, WEIRD_KEYS
from validation import Keystroke, Keypress, Log, KeystrokeDecoder, KeystrokeEncoder, is_key_valid
from typing import List, Optional, Union

class KeyLogger:
    """
    A class used to log keystrokes and calculate delays between each keypress.
    This class is responsible for capturing and storing keystrokes values and timings.
    It also keeps track of the total number of words typed and the entire string of characters typed.
    """

    def __init__(self, filename: Optional[str] = None) -> None:
        """
        Initialize the KeyLogger with a filename.
        Set attributes using the reset function.

        Args:
            filename (str, optional): The name of the file where the logs will be stored. 
            If not provided, the default file path (ABSOLUTE_REG_FILEPATH) will be used. 
            If a relative path is provided, it will be converted to an absolute path.
        """
        if filename is None:
            filename = ABSOLUTE_REG_FILEPATH
        else:
            # Make absolute path if not already
            if not path.isabs(filename):
                filename = path.join(ROOT, filename)

        self.filename: str = filename
        self.reset()

    def reset(self) -> None:
        """
        Clear the current state of the logger.
        Keystrokes, the typed string, and the word count will be set to default values.
        """
        # Keystroke related attributes
        self.keystrokes: List[Keystroke] = []
        self.typed_string: str = ""
        self.word_count: int = 0

        # Time related attribute
        self.prev_time: float = time() # The time at keypress is compared to this value.

    # on_press still needs to be tidied up a bit
    def on_press(self, keypress: Keypress) -> None:
        """
        Handles key press events and logs valid Keystroke events.

        This function is called whenever a key is pressed. 
        It validates the keypres and appends the data
        KeyLogger attributes modified: keystrokes, typed_string, word_count, prev_time

        Args:
            keypress (Keypress): The key press event to handle.
        """

        current_time = time()
        time_diff = current_time - self.prev_time
        if time_diff > 3:
            time_diff = 3 + (time_diff / 1000)
        key_as_string = str(keypress)
        if is_key_valid(keypress):
            # Mark first character time_diff as None
            if self.keystrokes == []:
                self.keystrokes.append(Keystroke(key_as_string, None))
            else:
                time_diff = round(time_diff, 4)  # Round to 4 decimal places
                self.keystrokes.append(Keystroke(key_as_string, time_diff))
            self.prev_time = current_time

            # Append typed character to the string
            if isinstance(keypress, KeyCode) and keypress.char is not None:
                self.typed_string += keypress.char
            elif keypress == Key.space:
                self.typed_string += ' '
                self.word_count += 1
            # logic for backspaces, including if going back on a space
            elif keypress == Key.backspace:
                self.typed_string = self.typed_string[:-1]
                if len(self.typed_string) > 0 and self.typed_string[-1]  == ' ':
                    self.word_count -= 1
            ## Enter/Tab not valid special keys, this may technically affect correctness of word count
            # elif keypress == Key.enter:
            #     # My logic is that spamming newlines should increase word count, but maybe just space is best
            #     self.typed_string += '\n'
            #     self.word_count += 1
            # elif keypress == Key.tab:
            #     self.typed_string += '\t'
            #     self.word_count += 1
        return None

    def stop_listener_condition(self, keypress: Keypress) -> bool:
        """
        Function to determine whether to stop the listener.

        Args:
            keypress (Keypress): The key press event to handle.

        Returns:
            bool: True if the listener should stop, False otherwise.
        """
        if keypress == Key.esc:
            return True
        elif self.word_count >= MAX_WORDS:
            return False
        elif isinstance(keypress, KeyCode) and keypress.char is not None:
            return keypress.char == STOP_KEY
        return False
    
    def on_release(self, keypress: Keypress) -> Union[False, None]:
        """
        Handles key release events. Stop the listener when stop condition is met.

        Args:
            keypress (Keypress): The key press event to handle.

        Returns:
            False or None: False if the maximum word count is reached. This stops the listener.
        """
        if self.stop_listener_condition(keypress):
            print('')
            return False
        return None

    def start_listener(self) -> None:
        """
        Function to start the key listener.
        The listener will only stop when stop_listener_condition returns True.
        """
        try:
            with Listener(on_press=self.on_press, on_release=self.on_release) as listener: # type: ignore
                print(f"Listener started. Type your text. The listener will stop after {MAX_WORDS} words have been typed or when you press ESC.")
                listener.join()
        except Exception as e:
            print(f"An error occurred: {e}")

    def is_log_legit(self, keystrokes: List[Keystroke], input_string: str) -> bool:
        """
        Validates the input string and keystrokes to ensure well formatted Log.

        This function ensures keystrokes are correctly formatted and input string is nonempty.

        Args:
            keystrokes (List[Keystroke]): The list of keystrokes to validate.
            input_string (str): The input string to validate.

        Returns:
            bool: True if the input is valid Log material, False otherwise.
        """
        if input_string == "":
            print("No keystrokes found. Log not legit")
            return False
        none_count = 0
        for keystroke in keystrokes:
            key = keystroke.key
            time_diff = keystroke.time
            if time_diff is None:
                none_count += 1
                if none_count > 1:
                    print('None value marks first character. Only use once.')
                    return False
            elif type(key) != str or type(time_diff) != float:
                print('Invalid keystrokes. Format is (key:str, time:float)')
                return False
        return True

    def set_internal_log(self, keystrokes: List[Keystroke], input_string: str) -> bool:
        """
        Replace the internal log with the provided keystrokes and input string.

        Args:
            keystrokes (List[Keystroke]): The list of keystrokes to replace self.keystrokes with.
            input_string (str): The input string to replace self.typed_string with.

        Returns:
            bool: True if state successfully replaced. False if arguments invalid.
        """
        if self.is_log_legit(keystrokes, input_string) == False:
            print("Invalid log. Internal log not set")
            return False
        self.keystrokes = keystrokes
        self.typed_string = input_string
        self.word_count = input_string.count(' ')
        return True

    def save_log(self, reset: bool = False) -> bool:
        """
        Function to save the log to a file.

        Args:
            reset (bool, optional): Whether to reset the logger after saving the log. Defaults to False.

        Returns:
            bool: True if the log was saved successfully, False otherwise.
        """
        if self.typed_string == "":
            print("No keystrokes to save.")
            if reset:
                self.reset()
            return False
        # ensure log is legit
        if self.is_log_legit(self.keystrokes, self.typed_string) == False:
            print("Log is not legit. Did not update file.")
            return False
        
        # Create a unique ID
        unique_id = str(uuid.uuid4())

        # Create the log object of class Log
        log: Log = {
            'id': unique_id,
            'string': self.typed_string,
            'keystrokes': self.keystrokes
        }
        # Fix the keystrokes
        # Append the log object to the file
        try:
            with open(self.filename, 'r+') as f:
                logs = json.load(f, cls=KeystrokeDecoder)
                logs.append(log)
                f.seek(0)
                json.dump(logs, f, cls=KeystrokeEncoder)
                print("Logfile updated.")
        except FileNotFoundError:
            with open(self.filename, 'w') as f:
                json.dump([log], f, cls=KeystrokeEncoder)
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        if reset:
            self.reset()
        return True
    
    def simulate_keystrokes(self, keystrokes: Optional[List[Keystroke]] = None) -> None:
        """
        Function to simulate the given keystrokes.

        Args:
            keystrokes (List[Keystroke], optional): The list of keystrokes to simulate. 
            If not provided, the internal keystrokes will be simulated.
        """
        if keystrokes is None:
            keystrokes = self.keystrokes
        # Validate keystrokes
        # Maybe keystrokes have to be legit to even be passed here?
        if keystrokes == []:
            print("No keystrokes found.")
            return

        keyboard = Controller()
        try:
            with Listener(on_release=self.on_release) as listener: # type: ignore
                print(f"Listener started. The simulation will start when you press ESC.")
                listener.join()
        except Exception as e:
            print(f"An error occurred: {e}")
        none_count = 0
        for keystroke in keystrokes:
            key = keystroke.key
            time = keystroke.time

            if is_key_valid(key) == False:
                print(f"Invalid key: {key}")
                continue
            if time is None:
                none_count += 1
                if none_count > 1:
                    print('Critical error: None value marks first character. Only use once')
                    break
                # What should this time diff be?
                time_diff = 0.0
            else:
                time_diff = time
                # If time difference is greater than 3 seconds, set diff to 3.x seconds with decimal coming from time_diff
                if SPEEDHACK:
                    if SPEED_MULTIPLE > 0:
                        time_diff = time_diff / SPEED_MULTIPLE
                if time_diff > 3:
                    time_diff = 3 + (time_diff / 1000)
            try:
                if time_diff > 0:
                    sleep(time_diff)  # Wait for the time difference between keystrokes
                if key in SPECIAL_KEYS:
                    keyboard.press(SPECIAL_KEYS[key])
                    keyboard.release(SPECIAL_KEYS[key])
                elif key in WEIRD_KEYS:
                    keyboard.type(WEIRD_KEYS[key])
                else:
                    keyboard.type(key.strip("\'"))  # Type the character
            except Exception as e:
                print(f"An error occurred: {e}")
                break

    def simulate_from_id(self, identifier: str) -> None:
        """
        Function to load a log given a UUID or a string.
        """
        try:
            with open(self.filename, 'r') as f:
                logs = json.load(f)
                for log in logs:
                    if log['id'] == identifier or log['string'] == identifier:
                        self.simulate_keystrokes(log['keystrokes'])
                        return
                print(f"No log found with the identifier: {identifier}")
        except FileNotFoundError:
            print("No log file found.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    logger = KeyLogger()
    logger.start_listener()
    success = logger.save_log()
    if success:
        print("\nLog saved. Now simulating keystrokes...\n")
        logger.simulate_keystrokes()

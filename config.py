from os import path
from pynput.keyboard import Key
ROOT = path.dirname(path.abspath(__file__)) # Get the absolute path of the current script
LOG_DIR = path.join(ROOT, "Logfiles") # Define the path for the logfiles directory
# Define the paths for the logfiles
ABSOLUTE_REG_FILEPATH = path.join(LOG_DIR, "keystrokes.json")
ABSOLUTE_SIM_FILEPATH = path.join(LOG_DIR, "simulated-keystrokes.json")

# Keyboard Listener timeout duration in seconds
LISTEN_TIMEOUT_DURATION = 30

### SIMULATION.PY CONFIG ###
SIM_MAX_DURATION = 30
SIM_DISABLE = False

SIM_DELAY_MEAN = 0.06
SIM_DELAY_STD_DEV = 0.015
SIM_MAX_WORDS = 300
MIN_DELAY = 0.03

SIM_ALLOW_ENTER_AND_TAB = True
SIM_SPEED_MULTIPLE = 5

### KEYLOGGER.PY CONFIG ###
MAX_WORDS = 50
SPEEDHACK = True # Only applies for KeyLogger class, this will be changed
STOP_KEY = "*" # This key is used to stop the listener when pressed

ROUND_DIGITS = 4 # This is for logfile timestamps

# *** KEY VALIDATION ***
SHIFT_SPEED = 0.2222
SHIFTED_CHARS = r'~!@#$%^&*()_+{}|:"<>?'

# The below constant is used by the functions: config.is_key_valid, KeySimulator.simulate_keystrokes, and KeyLogger.on_press
SPECIAL_KEYS = {
    'Key.space': Key.space,
    'Key.backspace': Key.backspace,
    'Key.shift': Key.shift,
    'Key.caps_lock': Key.caps_lock,
    'Key.tab': Key.tab,
    'Key.enter': Key.enter,
    }
BANNED_KEYS = ["'√'"]
WEIRD_KEYS = { # Quirks of str(keypress) when the keypress is backslash or apostrophe
#   str(KeyCode.from_char('\\')) == "'\\\\'"
#   str(KeyCode.from_char("'")) == '"\'"'
    "'\\\\'": '\\', # str(Key.backslash) -> '\\'
    '"\'"': "'" # This is an apostrophe
}

if SIM_ALLOW_ENTER_AND_TAB:
    sim_whitespace_dict = {
        '\n': Key.enter,
        '\t': Key.tab,
        ' ': Key.space,
    }
    sim_encoded_char_dict = {
        ' ': str(Key.space),
        '\t': str(Key.tab),
        '\n': str(Key.enter),
        '\\': "'\\\\'",
        "'": '"\'"'
    }
else:
    sim_whitespace_dict = {' ': Key.space}
    sim_encoded_char_dict = {
        ' ': str(Key.space),
        '\\': "'\\\\'",
        "'": '"\'"'
    }
    
### JSON format for keystrokes.json
# [
#   {
#     "id": "string",
#     "string": "string",
#     "keystrokes": [
#       ["string", number]
#     ]
#   }
# ]
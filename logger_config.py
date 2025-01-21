import time
import os

# ANSI escape codes
yellow_background = "\033[43m"
green_background = "\033[42m"
dark_green_background = "\033[48;5;22m"
blue_background = "\033[44m"
red_background = "\033[41m"
bold_white_text = "\033[1;37m"
underline_text = "\033[4m"  # Underline text
reset_formatting = "\033[0m"
dark_pink_background = "\033[48;5;52m"
light_pink_background = "\033[48;5;217m"
pink_background = "\033[48;5;212m"
bright_purple_background = "\033[48;5;129m"
dark_purple_background = "\033[48;5;54m"

DIGITS = {
    '1': [
        "    ███    ",
        " ██████    ",
        "    ███    ",
        "    ███    ",
        "    ███    ",
        "    ███    ",
        " ████████  "
    ],
    '2': [
        "██████████ ",
        "██      ██ ",
        "        ██ ",
        "██████████ ",
        "██         ",
        "██      ██ ",
        "██████████ "
    ],
    '3': [
        "██████████ ",
        "██      ██ ",
        "        ██ ",
        "   ███████ ",
        "        ██ ",
        "██      ██ ",
        "██████████ "
    ],
    '4': [
        "██      ██ ",
        "██      ██ ",
        "██      ██ ",
        "██████████ ",
        "        ██ ",
        "        ██ ",
        "        ██ "
    ],
    '5': [
        "██████████ ",
        "██         ",
        "██         ",
        "██████████ ",
        "        ██ ",
        "██      ██ ",
        "██████████ "
    ],
    '6': [
        "██████████ ",
        "██         ",
        "██         ",
        "██████████ ",
        "██      ██ ",
        "██      ██ ",
        "██████████ "
    ],
    '7': [
        "██████████ ",
        "        ██ ",
        "        ██ ",
        "        ██ ",
        "        ██ ",
        "        ██ ",
        "        ██ "
    ],
    '8': [
        "██████████ ",
        "██      ██ ",
        "██      ██ ",
        "██████████ ",
        "██      ██ ",
        "██      ██ ",
        "██████████ "
    ],
    '9': [
        "██████████ ",
        "██      ██ ",
        "██      ██ ",
        "██████████ ",
        "        ██ ",
        "        ██ ",
        "██████████ "
    ],
    '0': [
        "███████████ ",
        "██       ██ ",
        "██       ██ ",
        "██       ██ ",
        "██       ██ ",
        "██       ██ ",
        "███████████ "
    ]
}

SAD_FACE = [
    "     ██████████████     ",
    "   ██              ██   ",
    " ██                  ██ ",
    "██   ████      ████   ██",
    "██   ████      ████   ██",
    "██                    ██",
    "██                    ██",
    "██     ██████████     ██",
    " ██     ████████     ██ ",
    "   ██              ██   ",
    "     ██████████████     "
]

columns = 100
try:
    columns, _ = os.get_terminal_size()
except:
    pass

def custom_print(start, msg, end, seconds=0, overwrite=False):
    try:
        if overwrite:
            print("\033[F" * 3)
            print(f'\033[K{start}{msg}{end}')
        else:
            print(f'{start}{msg}{end}')

        if seconds > 0:
            for i in range(seconds, 0, -1):
                lineCount = 0
                for lineCount in range(7):
                    line = ''.join(DIGITS[digit][lineCount] for digit in str(i))  # Create the line for all digits
                    print(f'\033[K{start}{line}{end}')  # Clear the line and print
                time.sleep(1)
                if i > 1:
                    print("\033[F" * 8)
    except Exception as e:
        print(f"Error: {e}")

def printLine():
    dash = "-"
    for i in range(columns-2):
        dash += "-"
    custom_print('', dash, '')

def debug(msg, seconds=0, overwrite=False):
    custom_print(f"{dark_green_background}{bold_white_text}", f"{msg}", f"{reset_formatting}", seconds, overwrite)
    printLine()

def info(msg, seconds=0, overwrite=False):
    custom_print(f"{bright_purple_background}{bold_white_text}", f"{msg}", f"{reset_formatting}", seconds, overwrite)
    printLine()

def warning(msg, seconds=0):
    custom_print(f"{pink_background}{bold_white_text}", f"{msg}", f"{reset_formatting}", seconds)
    printLine()

def success(msg, seconds=0):
    custom_print(f"{blue_background}{bold_white_text}", f"{msg}", f"{reset_formatting}", seconds)
    printLine()

def error(msg, seconds=0):
    custom_print(f"{red_background}{bold_white_text}", f"{msg}", f"{reset_formatting}", seconds)

    for line in SAD_FACE:
        custom_print(f"{red_background}{bold_white_text}", line, f"{reset_formatting}")

    printLine()

# Usage example
if __name__ == "__main__":
    warning("This is an warning message")

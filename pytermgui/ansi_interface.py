"""
pytermgui.ansi_interface
------------------------
author: bczsalba


Various functions to interface with the terminal, using ANSI sequences.
Note:
    While most of these are universal on all modern terminals, there might
    be some that don't always work. I'll try to mark these separately.

    Also, using the escape sequence for save/restore of terminal doesn't work,
    only tput does. We should look into that.

Credits:
    - https://wiki.bash-hackers.org/scripting/terminalcodes
    - https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
"""
# pylint: disable=too-few-public-methods, arguments-differ


from typing import Optional, Any, Union
from subprocess import run as _run
from subprocess import Popen as _Popen
from sys import stdout as _stdout
from os import name as _name
from os import get_terminal_size

from .input import getch


__all__ = [
    "Color16",
    "Color256",
    "ColorRGB",
    "screen_size",
    "screen_width",
    "screen_height",
    "save_screen",
    "restore_screen",
    "start_alt_buffer",
    "end_alt_buffer",
    "clear",
    "hide_cursor",
    "show_cursor",
    "save_cursor",
    "restore_cursor",
    "report_cursor",
    "move_cursor",
    "cursor_up",
    "cursor_down",
    "cursor_right",
    "cursor_left",
    "cursor_next_line",
    "cursor_prev_line",
    "cursor_column",
    "cursor_home",
    "do_echo",
    "dont_echo",
    "set_mode",
    "report_mouse",
    "print_to",
    "reset",
    "bold",
    "dim",
    "italic",
    "underline",
    "blinking",
    "inverse",
    "invisible",
    "strikethrough",
    "foreground16",
    "background16",
    "foreground256",
    "background256",
    "foregroundRGB",
    "backgroundRGB",
]


class _Color:
    """Parent class for Color objects"""

    def __init__(self, layer: int = 0) -> None:
        """Set layer"""

        if layer not in [0, 1]:
            raise NotImplementedError(
                f"Layer {layer} is not supported for Color256 objects! Please choose from 0, 1"
            )

        self.layer_offset = layer * 10

    def __call__(
        self,
        text: str,
        color: Union[
            int, str, tuple[Union[int, str], Union[int, str], Union[int, str]]
        ],
    ) -> str:
        """Return colored text with reset code at the end"""

        if not isinstance(color, tuple):
            color = str(color)

        color_value = self.get_color(color)
        if color_value is None:
            return text

        return color_value + text + set_mode("reset")

    def get_color(self, attr: Any) -> Optional[str]:
        """This method needs to be overwritten."""

        _ = self
        return str(attr)


class Color16(_Color):
    """Class for using 16-bit colors"""

    def __init__(self, layer: int = 0) -> None:
        """Set up _colors dict"""

        super().__init__(layer)

        self._colors = {
            "black": 30,
            "red": 31,
            "green": 32,
            "yellow": 33,
            "blue": 34,
            "magenta": 35,
            "cyan": 36,
            "white": 37,
        }

    def __getattr__(self, attr: str) -> Optional[str]:
        return self.get_color(attr)

    def get_color(self, attr: str) -> Optional[str]:
        """Overwrite __getattr__ to look in self._colors"""

        if str(attr).isdigit():
            if not 30 <= int(attr) <= 37:
                raise ValueError("16-bit color values have to be in the range 30-37.")

            color = int(attr)

        else:
            color = self._colors[attr]

        return f"\033[{color+(self.layer_offset)}m"


class Color256(_Color):
    """Class for using 256-bit colors"""

    def get_color(self, attr: str) -> Optional[str]:
        """Return color values"""

        if not attr.isdigit():
            return None

        if not 1 <= int(attr) <= 255:
            return None

        return f"\033[{38+self.layer_offset};5;{attr}m"


class ColorRGB(_Color):
    """Class for using RGB or HEX colors

    Note:
        This requires a true-color terminal, like Kitty or Alacritty."""

    @staticmethod
    def _translate_hex(color: str) -> tuple[int, int, int]:
        """Translate hex string to rgb values"""

        if color.startswith("#"):
            color = color[1:]

        rgb = []
        for i in (0, 2, 4):
            rgb.append(int(color[i : i + 2], 16))

        return rgb[0], rgb[1], rgb[2]

    def get_color(self, colors: Union[str, tuple[int, int, int]]) -> Optional[str]:
        """Get RGB color code"""

        if isinstance(colors, str):
            colors = self._translate_hex(colors)

        if not len(colors) == 3:
            return None

        for col in colors:
            if not str(col).isdigit():
                return None

        strings = [str(col) for col in colors]
        return f"\033[{38+self.layer_offset};2;" + ";".join(strings) + "m"


# helpers
def _tput(command: list[str]) -> None:
    """Shorthand for tput calls"""

    waited_commands = [
        "clear",
        "smcup",
        "cup",
    ]

    command.insert(0, "tput")
    str_command = [str(c) for c in command]

    if command[1] in waited_commands:
        _run(str_command, check=True)
        return

    _Popen(str_command)


# screen commands
def screen_size() -> tuple[int, int]:
    """Get screen size using os module

    This is technically possible using a method of
    moving the cursor to an impossible location, and
    using `report_cursor()` to get where the position
    was clamped, but it messes with the cursor position
    and makes for glitchy printing.
    """

    # save_cursor()
    # move_cursor((9999, 9999))
    # size = report_cursor()
    # restore_cursor()
    # return size

    return get_terminal_size()


def screen_width() -> int:
    """Get screen width"""

    size = screen_size()

    if size is None:
        return 0
    return size[0]


def screen_height() -> int:
    """Get screen height"""

    size = screen_size()

    if size is None:
        return 0
    return size[1]


def save_screen() -> None:
    """Save the contents of the screen, wipe.
    Use `restore_screen()` to get them back."""

    # print("\033[?47h")
    _tput(["smcup"])


def restore_screen() -> None:
    """Restore the contents of the screen,
    previously saved by a call to `save_screen()`."""

    # print("\033[?47l")
    _tput(["rmcup"])


def start_alt_buffer() -> None:
    """Start alternate buffer that is non-scrollable"""

    print("\033[?1049h")


def end_alt_buffer() -> None:
    """Return to main buffer from alt, restoring state"""

    print("\033[?1049l")


def clear(what: str = "screen") -> None:
    """Clear specified region

    Available options:
        - screen - clear whole screen and go home
        - bos    - clear screen from cursor backwards
        - eos    - clear screen from cursor forwards
        - line   - clear line and go to beginning
        - bol    - clear line from cursor backwards
        - eol    - clear line from cursor forwards

    """

    commands = {
        "eos": "\033[0J",
        "bos": "\033[1J",
        "screen": "\033[2J",
        "eol": "\033[0K",
        "bol": "\033[1K",
        "line": "\033[2K",
    }

    _stdout.write(commands[what])


# cursor commands
def hide_cursor() -> None:
    """Don't print cursor"""

    # _tput(['civis'])
    print("\033[?25l")


def show_cursor() -> None:
    """Set cursor printing back on"""

    # _tput(['cvvis'])
    print("\033[?25h")


def save_cursor() -> None:
    """Save cursor position, use `restore_cursor()`
    to restore it."""

    # _tput(['sc'])
    _stdout.write("\033[s")


def restore_cursor() -> None:
    """Restore cursor position saved by `save_cursor()`"""

    # _tput(['rc'])
    _stdout.write("\033[u")


def report_cursor() -> Optional[tuple[int, int]]:
    """Get position of cursor"""

    print("\033[6n")
    chars = getch()
    posy, posx = chars[2:-1].split(";")

    if not posx.isdigit() or not posy.isdigit():
        return None

    return int(posx), int(posy)


def move_cursor(pos: tuple[int, int]) -> None:
    """Move cursor to pos"""

    posx, posy = pos
    _stdout.write(f"\033[{posy};{posx}H")


def cursor_up(num: int = 1) -> None:
    """Move cursor up by `num` lines"""

    _stdout.write(f"\033[{num}A")


def cursor_down(num: int = 1) -> None:
    """Move cursor down by `num` lines"""

    _stdout.write(f"\033[{num}B")


def cursor_right(num: int = 1) -> None:
    """Move cursor left by `num` cols"""

    _stdout.write(f"\033[{num}C")


def cursor_left(num: int = 1) -> None:
    """Move cursor left by `num` cols"""

    _stdout.write(f"\033[{num}D")


def cursor_next_line(num: int = 1) -> None:
    """Move cursor to beginning of num-th line down"""

    _stdout.write(f"\033[{num}E")


def cursor_prev_line(num: int = 1) -> None:
    """Move cursor to beginning of num-th line down"""

    _stdout.write(f"\033[{num}F")


def cursor_column(num: int = 0) -> None:
    """Move cursor to num-th column in the current line"""

    _stdout.write(f"\033[{num}G")


def cursor_home() -> None:
    """Move cursor to HOME"""

    _stdout.write("\033[H")


def set_mode(mode: Union[str, int]) -> str:
    """Set terminal display mode

    Available options:
        - reset         (0)
        - bold          (1)
        - dim           (2)
        - italic        (3)
        - underline     (4)
        - blink         (5)
        - inverse       (7)
        - invisible     (8)
        - strikethrough (9)

    You can use both the digit and text forms."""

    options = {
        "reset": 0,
        "bold": 1,
        "dim": 2,
        "italic": 3,
        "underline": 4,
        "blink": 5,
        "inverse": 7,
        "invisible": 8,
        "strikethrough": 9,
    }

    if not str(mode).isdigit():
        mode = options[str(mode)]

    code = f"\033[{mode}m"
    _stdout.write(code)

    return code


def do_echo() -> None:
    """Echo user input"""

    if not _name == "posix":
        raise NotImplementedError("This method is only implemented on POSIX systems.")

    _Popen(["stty", "echo"])


def dont_echo() -> None:
    """Don't echo user input"""

    if not _name == "posix":
        raise NotImplementedError("This method is only implemented on POSIX systems.")

    _Popen(["stty", "-echo"])


def report_mouse(
    event: str, method: Optional[str] = "decimal_xterm", action: Optional[str] = "start"
) -> None:
    """Start reporting mouse events

    options:
        - press_release
        - highlight
        - press
        - movement

    methods:
        None:          limited in coordinates, not recommended.
        decimal_xterm: default, most universal
        decimal_urxvt: older, less compatible
        decimal_utf8:  apparently not too stable

    more information: https://stackoverflow.com/a/5970472
    """

    if event == "press_release":
        _stdout.write("\033[?1000")

    elif event == "highlight":
        _stdout.write("\033[?1001")

    elif event == "press":
        _stdout.write("\033[?1002")

    elif event == "movement":
        _stdout.write("\033[?1003")

    else:
        raise NotImplementedError(f"Mouse report event {event} is not supported!")

    _stdout.write("h" if action == "start" else "l")

    if method == "decimal_utf8":
        _stdout.write("\033[?1005")

    elif method == "decimal_xterm":
        _stdout.write("\033[?1006")

    elif method == "decimal_urxvt":
        _stdout.write("\033[?1015")

    elif method is None:
        return

    else:
        raise NotImplementedError(f"Mouse report method {method} is not supported!")

    _stdout.write("h" if action == "start" else "l")
    _stdout.flush()


# shorthand functions
def print_to(pos: tuple[int, int], *args: tuple[Any, ...]) -> None:
    """Print text to given position"""

    text = ""
    for arg in args:
        text += " " + str(arg)

    move_cursor(pos)
    print(text)


def reset() -> str:
    """Reset printing mode"""

    return set_mode("reset")


def bold(text: str) -> str:
    """Return text in bold"""

    return set_mode("bold") + text + reset()


def dim(text: str) -> str:
    """Return text in dim"""

    return set_mode("dim") + text + reset()


def italic(text: str) -> str:
    """Return text in italic"""

    return set_mode("italic") + text + reset()


def underline(text: str) -> str:
    """Return text underlined"""

    return set_mode("underline") + text + reset()


def blinking(text: str) -> str:
    """Return text blinking"""

    return set_mode("blink") + text + reset()


def inverse(text: str) -> str:
    """Return text inverse-colored"""

    return set_mode("inverse") + text + reset()


def invisible(text: str) -> str:
    """Return text in invisible"""

    return set_mode("invisible") + text + reset()


def strikethrough(text: str) -> str:
    """Return text as strikethrough"""

    return set_mode("strikethrough") + text + reset()


foreground16 = Color16()
background16 = Color16(layer=1)

foreground256 = Color256()
background256 = Color256(layer=1)

foregroundRGB = ColorRGB()
backgroundRGB = ColorRGB(layer=1)
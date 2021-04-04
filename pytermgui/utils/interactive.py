""" 
pytermgui.interactive 
---------------------

A submodule providing functions to call object methods interactively.

IMPORTANT: the object provided should have type annotations, otherwise
all arguments will be passed as plain strings.
"""

from .. import Label, Prompt, Container, InputField, bold, italic, color, highlight
from .  import basic_selection as selection
from .. import padding_label as padding
from .. import getch, set_style

# import utilities
from . import keys, wipe, width

# other imports
from inspect   import signature, _empty, Parameter
from typing    import Callable
from random    import randint
import re,sys
dunder = re.compile(r'__[a-z_]+__')


def create_picker_from(obj:object, ignored: dict=None):
    """ Create method picker from `obj` """

    picker    = Container(width=60)
    for i in range(4):
        picker.set_corner(i,'x')

    functions = [v for v in dir(obj) if callable(getattr(obj,v)) and not len(dunder.findall(v))]
    functions.sort()

    title     = Label(value=f'methods of {type(obj).__name__}')
    picker.add_elements([title,padding])

    for i,v in enumerate(functions):
        p = Prompt(label=v,padding=2)
        p.submit = lambda self: create_interactive_from(getattr(obj,self.label),ignored)
        picker.add_elements(p)

    picker.center()
    picker.select()
    print(picker)
    selection(picker)

def create_interactive_from(function:Callable, ignored: dict=None):
    """ 
    Create menu to take input from `function`.

    If any parameters if `function` are keys in `ignored`, use `ignored[key]`
    as a default value, and don't create a Prompt.
    """

    wipe()    
    main  = Container(width=60)
    sig   = signature(function)

    title = Label(f'calling function {function.__name__}')
    main.add_elements([title,padding])

    arguments = {}
    if not ignored:
        ignored = {}

    for i,(name,param) in enumerate(sig.parameters.items()):
        if name in ignored.keys():
            arguments[name] = ignored[name]
            continue
        else:
            arguments[name] = param.default

        if param.annotation == Callable:
            continue

        p = Prompt(label=name,value='',padding=2)
        p.param = param
        p.default = param.default
        p.annotation = param.annotation

        p.set_style('delimiter',lambda: ["<",">"])
        p.submit = lambda self: create_dialog_from(self.label,self.param,self)
        p.argument = True

        arguments[name] = p
        main.add_elements(p)
    main.arguments = arguments

    button = Prompt(options=['run!'])
    main.add_elements([padding,button])
    button.submit = lambda self: _run_function(function,main)

    main.center()
    main.select()
    print(main)

    selection(main)

def create_dialog_from(label:str, parameter:Parameter, parent:object):
    """
    Create input dialog menu, with title `label`, using data from `parameter`
    to figure out default values and such.

    Values get set on key `ENTER`, to `parent`.
    """

    wipe()
    dialog = Container(width=width())
    dialog.set_borders(' -')

    title = Label(f'value for {parameter.name}')
    dialog.add_elements([title,padding])

    if parent.real_value:
        default = parent.real_value
    elif parent.value:
        default = parent.value
    else:
        default = '' if parameter.default == _empty or not parameter.default else parameter.default
    field = InputField(default=str(default))
    dialog.add_elements(field)

    dialog.center()
    print(dialog)

    while True:
        key = getch()
        if key in ["ESC","SIGTERM"]:
            wipe()
            break

        elif key == "ENTER":
            parent.value = field.value
            wipe()
            break

        field.send(key)
        print(dialog)

def _run_function(function:Callable, obj:object ,callback: Callable=None):
    """
    Execute `function`, using arguments supplied by `obj`.

    Dict `obj` needs to have an attribute `arguments`, which stores default values
    or Prompt objects. This is generated by `create_dialog_from`.

    Executes `callback` with return of `function`.
    """

    args_list = []

    for name,e in obj.arguments.items():
        if hasattr(e,'argument'):
            if e.real_value:
                value = e.real_value
            elif e.value:
                value = e.value
            else:
                value = e.default

            if e.annotation == int:
                try:
                    value = int(float(value))
                except Exception as e:
                    print(e)
                    return

            elif e.annotation == bool:
                if isinstance(value,str):
                    if value.lower() in ["true","1"]:
                        value = True
                    else:
                        value = False

            args_list.append(value)
        else:
            args_list.append(e)

    args = tuple(args_list)

    wipe()
    ret = function(*args)

    if callback:
        callback(ret)

    return ret

def setup():
    """
    Setup visual styles for objects. This is likely only needed if you
    are running this without other setup, so you don't have styles set
    up.
    """

    accent1 = randint(17,230)
    accent2 = randint(17,230)
    set_style('prompt_long_highlight', lambda item: highlight(item,accent1))
    set_style('prompt_short_highlight', lambda item: highlight(item,accent1))
    set_style('prompt_delimiter',      lambda: None)
    set_style('container_border',      lambda item: bold(color(item,accent2)))
    set_style('label_value',           lambda item: bold(color(item,accent1)))
    wipe()
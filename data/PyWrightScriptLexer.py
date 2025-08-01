# A custom lexer for PyWright scripts, mainly for syntax highlighting
import re

from PyQt6.QtGui import QColor, QFont

from PyQt6.Qsci import QsciLexerCustom, QsciScintilla, QsciAPIs

from data import IDESettings, EditorThemes

commands = [
    # In the written order in doc.txt (with some additions):
    # "To add various objects"
    "emo",
    "gui", "Back", "Button", "Wait", "Input",
    "menu",
    "list", "li", "showlist", "forgetlist", "forgetlistitem",
    "present",
    "examine", "region",

    # "Various control commands"
    "print", "include", "nt", "goto", "label", "penalty", "pause", "timer", "waitenter",
    "mus", "sfx", "movie",
    "exit", "endscript", "casemenu", "script", "top",
    "cross", "endcross", "statement", "resume", "cross_restart", "clearcross",
    "next_statement", "prev_statement",

    # "Variables and flags to keep track of what happens"
    "setflag", "delflag", "flag", "noflag", "set",
    "setvar", "joinvar", "addvar", "subvar", "divvar", "mulvar", "absvar",
    "random", "getvar",
    "is", "isnot", "isempty", "isnotempty", "isnumber",
    "exportvars", "importvars", "savegame", "loadgame", "deletegame",

    # "Working with evidence"
    "addev", "delev",

    # "Special effects"
    "draw_off", "draw_on", "scroll", "rotate",

    # macros
    "macro", "endmacro",

    # data.txt fields
    "icon", "title", "author", "version",

    # "Animation file commands" (these can be added here too)
    "horizontal", "vertical", "length", "loops", "framedelay",
    "blinkmode", "blipsound", "framecompress",

    # "Art Types"
    "fg", "bg", "ev",

    # Not mentioned in doc.txt, but somewhere else
    "zoom", "char", "delete", "shake", "is_ex", "setvar_ex",

    # Not mentioned in doc.txt but in docs/index.html
    "filewrite", "screenshot", "bemo", "clear", "textblock", "textbox",
    "locked_cases", "addcase", "wincase", "resetcase", "examine3d", "localmenu", "region3d",
    "game", "controlanim", "globaldelay", "gamemenu", "getprop", "setprop", "debug",
    "fade", "grey", "invert", "tint", 

    # Misc. stuff (some might be custom macros, or stuff that wasn't in 0.9880)
    "in", "out", "obj"
]

special_variables = [
    # In the written order in doc.txt
    # "Used in actual game logic"
    "_speaking",

    # "Dev controls"
    "_debug", "_return", "_preload",

    # "Things engine sets which might be useful to use in logic"
    "_layer_invisible", "_layer_bg", "_layer_char", "_layer_fg", "_layer_textbox", "_layer_gui"
    "_speaking_name", "_lastline", "_currentline", "_lastlabel", "_currentlabel",
    "_statement", "_selected", "_examine_offset_x", "_examine_offset_y",
    "_examine_click_x", "_examine_click_y",

    # "Interface toggles so you can customize look or behavior of things"
    "_default_port_fg_delay", "_default_fg_frame_delay", "_list_checked_img", "_bigbutton_img",
    "_textbox_show_button", "_textbox_show_recordbutton", "_textbox_lines", "_textbox_wrap",
    "_textbox_allow_skip", "_textbox_skipupdate", "_nt_image", "_examine_skipupdate", "_examine_showbars",
    "_examine_showcursor", "_examine_use", "_examine_mousedown", "_testimony_blinker", "_cr_button",
    "_allow_present_evidence", "_allow_present_profiles", "_allow_click_save", "_allow_saveload",
    "_allow_click_load",

    # "Present customization"
    "_profiles_enable", "_profiles_present", "_evidence_enable", "_evidence_present",
    "_cr_back_button", "_list_back_button", "_menu_fade_level", "_double_screen_list_fade",
    "_flash_sound", "_shake_sound", "_music_loop",

    # "Used in intro.txt in the game folder to control menu"
    "_order_cases",

    # _case_0, _case_1, case_2... etc. are handled in a separate list
    # Misc. stuff that wasn't in the doc.txt (some might be custom macros, or stuff that wasn't in 0.9880)
    "_list_bg_image", "_music_fade", "ev_mode_bg_logic", "_bigbutton_bg",
    "_production", "_ev_pages", "_ev", "_version"
]

# Support up to 100 case definitions for a single game, this should be much more than enough.
cases = ["_case_{}".format(num) for num in range(100)]

# Just for that sweet, sweet startswith()
named_parameters = ("start=", "end=", "e=", "x=", "y=", "z=", "name=", "speed=", "width=", "height=", "rwidth=", "rheight=",
                    "graphic=", "graphichigh=", "examine=", "talk=", "present=", "move=", "fail=", "nametag=", "result=", "label=",
                    "mag=", "frames=", "hotkey=", "jumpto=","pause=","test=", "loops=", "rotz=", "be=", "pri=", "variable=", "threat=",
                    "delay=", "color=", "run=", "priority=", "prop=", "value=", "degrees=", "axis=", "filter=", "after=")

parameters = ["stack", "nowait", "noclear", "hide", "fade", "true", "false", "noback", "sx", "sy",
              "blink", "loop", "noloop", "b", "t", "stop", "noauto", "password", "all", "suppress", "flipx", "wait", "hold", "try_bottom",
              "script", "last", "both"]

# Following might need some sort of regex for each
# "{sound {str}}"
# "{c{number}}
# "{p{number}}
# "{delay {number}}
# "{sfx {str}}
# "{s {str}}"
string_tokens = ["{n}", "{next}", "{f}", "{center}"]

# Logical operators
logic_operators = ["==", "<=", ">=", "<", ">", "NOT", "AND", "OR"]

# Compiled regular expressions
# This regex also includes whitespace characters, due to how Scintilla's styling system works
# It only cares about the "word length" and the style it is gonna use.
_TOKEN_REGEX = re.compile(r"//+[^\r\n]*|#+[^\r\n]*|\{[^\r\n]*}|\"[^\r\n]*\"|\S+|\s+")

# This regex finds all the ? characters in a given string
_QUESTION_MARK_REGEX = re.compile(r"\?+")

def is_string_number(string: str) -> bool:
    if string.startswith("-"):
        return is_string_number(string[1:])

    return string.isnumeric() or is_string_float(string)


def is_string_float(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False


class PyWrightScriptLexer(QsciLexerCustom):

    def __init__(self, parent: QsciScintilla):
        super().__init__(parent)

        font_name = IDESettings.get_font_name()
        font_size = IDESettings.get_font_size()
        bold_font = IDESettings.get_font_boldness()

        self.set_editor_color_theme()

        self.set_font_properties(font_name, font_size, bold_font)

        self.builtin_macros: list[str] = []
        self.game_macros: list[str] = []
        
        self.setup_autocompletion()

    def setup_autocompletion(self):
        # Create an API for us to populate with our autocomplete terms
        api = QsciAPIs(self)

        # Add autocompletion strings
        for l in (commands, special_variables, named_parameters, parameters, string_tokens, logic_operators, self.builtin_macros, self.game_macros):
            for c in l:
                api.add(c)

        # Compile the api for use in the lexer
        api.prepare()

    def set_font_properties(self, font_name: str, font_size: int, bold_font: bool):
        self.setDefaultFont(QFont(font_name, font_size))
        font_weight = QFont.Weight.Bold if bold_font else QFont.Weight.Normal
        for i in range(0, 10):
            self.setFont(QFont(font_name, font_size, weight=font_weight), i)

    def set_builtin_macros(self, new_list: list[str]):
        self.builtin_macros = new_list
        self.setup_autocompletion()

    def set_game_macros(self, new_list: list[str]):
        self.game_macros = new_list
        self.setup_autocompletion()

    def set_editor_color_theme(self):
        # Default Text Settings
        self.setDefaultColor(QColor(EditorThemes.current_editor_theme.colors[0].text_color))
        self.setDefaultPaper(QColor(EditorThemes.current_editor_theme.colors[0].paper_color))

        for color_index in range(len(EditorThemes.current_editor_theme.colors)):
            self.setColor(QColor(EditorThemes.current_editor_theme.colors[color_index].text_color), color_index)
            self.setPaper(QColor(EditorThemes.current_editor_theme.colors[color_index].paper_color), color_index)

    def language(self):
        return "PyWright Script"

    def description(self, style):
        if style == 0:
            return "default_style"
        elif style == 1:
            return "commands_style"
        elif style == 2:
            return "special_variables_style"
        elif style == 3:
            return "parameters_style"
        elif style == 4:
            return "line_comments_style"
        elif style == 5:
            return "double_quoted_strings_style"
        elif style == 6:
            return "numbers_style"
        elif style == 7:
            return "builtin_macros_style"
        elif style == 8:
            return "game_macros_style"
        elif style == 9:
            return "stringtokens"
        else:
            return ""

    def styleText(self, start, end):
        self.startStyling(start)

        text = bytearray(self.parent().text(), "utf-8")[start:end].decode("utf-8")

        token_list = [(token, len(bytearray(token, "utf-8"))) for token in _TOKEN_REGEX.findall(text)]

        # Keep track if a token is a newline, to distinguish commands and parameters on the next token for the ones such as "fade" and "script":
        wasNewLine = True
        for i, token in enumerate(token_list):
            self._set_styling_for_token(token, wasNewLine)
            wasNewLine = '\n' in token[0].replace('\r', '\n') or (wasNewLine and not token[0].strip())

    def _set_styling_for_token(self, token: tuple[str, int], isFirstOfLine:bool = False):
        # Handle tokens ending with ?, except comments
        if token[0].endswith("?") and len(token[0]) > 1 and not (token[0].startswith("//") or token[0].startswith("#")):
            # Check if there are multiple question marks first

            question_marks = _QUESTION_MARK_REGEX.findall(token[0])

            if len(question_marks[0]) == 1:
                # end of a ? conditional, don't consider the ?
                token_split = token[0].rsplit("?", maxsplit=1)
                token_0_len = len(bytearray(token_split[0], "utf-8"))
                # process the token sans ?
                self._set_styling_for_token((token_split[0], token_0_len))
                # then the ? on its own
                self.setStyling(1, 2)
                return

        # Proceed through the tokens normally
        if token[0] in commands:
            # If a command token can also be a parameter (such as "fade" and "script"),
            # check if it is a the start of a line to know which coloration to perform:
            if token[0] in parameters and not isFirstOfLine:
                self.setStyling(token[1], 3)
                return
            self.setStyling(token[1], 1)
        elif token[0] in logic_operators:
            self.setStyling(token[1], 2)
        elif token[0] in special_variables or token[0] in cases:
            self.setStyling(token[1], 2)
        elif token[0].startswith("$") and (token[0][1:] in special_variables
                                           or token[0][1:] in parameters 
                                           or token[0][1:].isdigit()): # e.g. $1, $2, engine-level, used for accessing macro args
            self.setStyling(token[1], 2)
        elif token[0].startswith(named_parameters):
            # Divide the = section and then colorize that instead
            param_name = token[0].split("=", maxsplit=1)
            param_0_len = len(param_name[0]) + 1  # + 1 for the "="
            self.setStyling(param_0_len, 3)
            param_1_token = (param_name[1], len(param_name[1]))
            self._set_styling_for_token(param_1_token)
        elif token[0] in parameters:
            self.setStyling(token[1], 3)
        elif token[0].startswith("{") and "}" in token[0] and ' ' in token[0]:
            # macro call with a parameter

            #split token to make sure there is not more than one macro call
            tokens = re.findall('[^}]+}|[^}]+', token[0])
            if (len(tokens) > 1):
                # process all tokens separately
                for subtoken in tokens:
                    self._set_styling_for_token((subtoken, len(subtoken)))
                return
            
            token_split = token[0].split(' ')
            for tokenpiece in token_split:
                # first token is always the macro
                if tokenpiece == token_split[0]:
                    self.setStyling(len(token_split[0]) + 1, 3)
                    continue
                #last token needs special handling for the closing bracket
                elif tokenpiece.endswith("}"):
                    tokenpiece_split = tokenpiece.split("}", maxsplit=1)
                    # process the last token sans bracket
                    self._set_styling_for_token((tokenpiece_split[0], len(tokenpiece_split[0])))
                    # then the bracket by itself
                    self._set_styling_for_token(("}", 1))
                    break
                # middle tokens get processed normally
                self._set_styling_for_token((tokenpiece, len(tokenpiece) + 1))
        elif token[0] == "}" or token[0].startswith("{") and token[0].endswith("}"):
            self.setStyling(token[1], 3)
        elif token[0].startswith("//") or token[0].startswith("#"):
            self.setStyling(token[1], 4)
        elif token[0].startswith("\"") and token[0].endswith("\""):
            self._set_styling_for_string_token(token[0])
        elif is_string_number(token[0]):
            self.setStyling(token[1], 6)
        elif token[0] in self.builtin_macros:
            self.setStyling(token[1], 7)
        elif token[0] in self.game_macros:
            self.setStyling(token[1], 8)
        else:
            self.setStyling(token[1], 0)

    def _set_styling_for_string_token(self, text: str):
        # Note: text should have a " at start and at end.
        
        # Loop while there is text to style
        while len(text) > 0:

            # Search for braces
            openPos = text.find("{", 1)
            closePos = text.find("}", 1)

            # Take the next found brace (need to take into account the fact that not found returns -1 and -1 is < 0)
            if openPos < 0:
                nextPos = closePos
            elif closePos < 0:
                nextPos = openPos
            else:
                nextPos = min(openPos, closePos)

            # {} are not found: place only string
            if openPos < 0 and closePos < 0:
                self.setStyling(len(bytearray(text, "utf-8")), 5)
                break

            else:
                # Split text
                token = text[:nextPos]
                text = text[nextPos:]
                
                # Apply style
                # If token starts with { and text with }, put the } in the token and colorize it a different color
                if token.startswith('{') and text.startswith('}'):
                    token = token + text[0]
                    text = text[1:]
                    self.setStyling(len(bytearray(token, "utf-8")), 9)
                else:
                    self.setStyling(len(bytearray(token, "utf-8")), 5)



# Holds the information regarding a macro in PyWright,
# Like its name, location, and type (builtin, game, case, file)

from enum import Enum
from pathlib import Path

class MacroLocationType(Enum):
    BUILTIN = 0
    GAME = 1
    CASE = 2
    FILE = 3

class PyWrightMacro:

    def __init__(self, name:str, path: Path, line: int, kind: MacroLocationType):
        self._name = name
        self._path = path
        self._line = line
        self._kind = kind

    def name(self) -> str:
        return self._name

    def path(self) -> Path:
        return self._path

    def line(self) -> int:
        return self._line

    def kind(self) -> MacroLocationType:
        return self._kind

    def __repr__(self):
        return "PyWrightMacro(%r, %r, %r, %r)"%(self._name, self._path, self._line, self._kind)

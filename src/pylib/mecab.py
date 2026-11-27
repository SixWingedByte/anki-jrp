# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/; © 2022 Ben Kerman
import ctypes
import os
import platform
import subprocess
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from subprocess import PIPE, Popen
from typing import Iterable, List, Optional, Tuple

from .normalize import is_kana, to_hiragana


class MecabError(Exception):
    pass


@dataclass
class ParserUnit:
    value: str

    def __repr__(self):
        return f"InputUnit[{self.value}]"


class HinsiType(Enum):
    ZYOSI = auto()
    YOUGEN = auto()
    SETUBI = auto()
    SYMBOL = auto()
    NUMBER = auto()
    OTHER = auto()


@dataclass
class MecabUnit(ParserUnit):
    hinsi: str
    hinsi_class_1: Optional[str] = None
    hinsi_class_2: Optional[str] = None
    hinsi_class_3: Optional[str] = None
    conj_type: Optional[str] = None
    conj_form: Optional[str] = None
    base_form: Optional[str] = None
    reading: Optional[str] = None
    pronunciation: Optional[str] = None

    def __repr__(self):
        return "MecabUnit[" \
               f"{self.value}:" \
               f"{self.hinsi}," \
               f"{self.hinsi_class_1}," \
               f"{self.hinsi_class_2}," \
               f"{self.hinsi_class_3}," \
               f"{self.conj_type}," \
               f"{self.conj_form}," \
               f"{self.base_form}," \
               f"{self.reading}," \
               f"{self.pronunciation}]"

    def hinsi_type(self) -> HinsiType:
        if self.hinsi == "助詞" or self.hinsi == "助動詞":
            return HinsiType.ZYOSI
        elif self.hinsi == "動詞" or self.hinsi == "形容詞":
            return HinsiType.YOUGEN
        elif self.hinsi == "記号":
            return HinsiType.SYMBOL
        elif self.hinsi == "名詞":
            if self.hinsi_class_1 == "接尾":
                return HinsiType.SETUBI
            elif self.hinsi_class_1 == "数":
                return HinsiType.NUMBER
        return HinsiType.OTHER

    def comp_hinsi(self, *args: str):
        if self.hinsi != args[0]:
            return False
        if len(args) > 1 and self.hinsi_class_1 != args[1]:
            return False
        if len(args) > 2 and self.hinsi_class_2 != args[2]:
            return False
        if len(args) > 3 and self.hinsi_class_3 != args[3]:
            return False
        return True

    def base_reading(self) -> Optional[str]:
        if self.hinsi_type() != HinsiType.YOUGEN:
            return None

        if is_kana(self.base_form):
            return self.base_form

        itr = enumerate(zip(reversed(self.value), reversed(self.reading)))
        for i, (co, cr) in itr:
            if co != cr:
                break
        else:
            return None

        return self.reading[0:len(self.reading) - i] + self.base_form[len(self.value) - i:]

    @classmethod
    def from_line(cls, line: str) -> Tuple["MecabUnit", int, int]:
        def raise_on_ast(val: str) -> str:
            if val == "*":
                raise MecabError("unexpected empty value in unit")
            else:
                return val

        def ast_to_none(val: str) -> Optional[str]:
            return None if val == "*" else val

        # format: %m(表層形)\t%ps,%pe,%H(品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用型,活用形,原形,読み,発音)
        orig: str
        data: str
        try:
            orig, data = line.split("\t", 1)
        except ValueError:
            raise MecabError(f"invalid line: {line}")

        fields = data.split(",")
        if len(fields) < 3 or (fields[2] != "未知語" and len(fields) != 11):
            raise MecabError(f"invalid number of fields: {line}")

        if fields[2] != "未知語":
            obj = cls(orig, fields[2],
                      ast_to_none(fields[3]),
                      ast_to_none(fields[4]),
                      ast_to_none(fields[5]),
                      ast_to_none(fields[6]),
                      ast_to_none(fields[7]),
                      raise_on_ast(fields[8]),
                      to_hiragana(raise_on_ast(fields[9])),
                      to_hiragana(raise_on_ast(fields[10])))
        else:
            obj = cls(orig, fields[2])
        return obj, int(fields[0]), int(fields[1])


_NODE_FORMAT = "%m\\t%ps,%pe,%H\\n"
_UNK_FEATURE = "未知語"


def _units_from_output(utf8_bytes: bytes, lines: Iterable[str]) -> List[ParserUnit]:
    """Turns MeCab output lines (up to EOS) for utf8_bytes into units, keeping skipped whitespace."""
    units: List[ParserUnit] = []
    last_end = 0
    for line in lines:
        if line == "EOS":
            break
        unit, start, end = MecabUnit.from_line(line)
        if last_end != start:
            units.append(ParserUnit(utf8_bytes[last_end:start].decode("utf-8")))
        last_end = end
        units.append(unit)
    return units


@dataclass
class Mecab:
    exe_path: Optional[str] = None
    dic_dir: Optional[str] = None
    _inst: Optional[Popen] = field(default=None, init=False)

    def _instance(self) -> Popen:
        if self._inst is None or self._inst.poll() is not None:
            env = os.environ.copy()
            args = [self.exe_path] if self.exe_path else ["mecab"]
            args.extend((f"--unk-feature={_UNK_FEATURE}", f"--node-format={_NODE_FORMAT}"))
            if self.exe_path:
                if platform.system() == "Linux":
                    env["LD_LIBRARY_PATH"] = os.path.dirname(self.exe_path)
                args.append(f"--rcfile={os.path.join(os.path.dirname(self.exe_path), 'mecabrc')}")
            if self.dic_dir:
                args.append(f"--dicdir={self.dic_dir}")

            try:
                if platform.system() == "Windows":
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                else:
                    si = None
                self._inst = Popen(args, stdin=PIPE, stdout=PIPE, env=env, startupinfo=si)
            except FileNotFoundError:
                raise MecabError("executable not found")

        return self._inst

    def analyze(self, txt: str) -> List[ParserUnit]:
        if "\n" in txt:
            raise MecabError("line feed in text passed to analyze function")

        inst = self._instance()
        utf8_bytes = txt.encode("utf-8")
        inst.stdin.write(utf8_bytes + b"\n")
        inst.stdin.flush()

        def read_lines():
            while True:
                yield inst.stdout.readline().rstrip(b"\r\n").decode("utf-8")

        return _units_from_output(utf8_bytes, read_lines())


def bundled_library_path(lib_dir: str, windows_bin_dir: str) -> Optional[str]:
    """The MeCab shared library bundled for this platform, or None if there's none."""
    system, machine = platform.system(), platform.machine().lower()
    if system == "Windows":
        # libmecab.dll next to mecab.exe is x86-64; it can't be loaded into ARM64 Python
        if machine in ("amd64", "x86_64") and ctypes.sizeof(ctypes.c_void_p) == 8:
            path = os.path.join(windows_bin_dir, "libmecab.dll")
        else:
            return None
    elif system == "Darwin":
        path = os.path.join(lib_dir, "libmecab-macos.dylib")  # universal: x86_64 + arm64
    elif system == "Linux" and machine in ("x86_64", "amd64"):
        path = os.path.join(lib_dir, "libmecab-linux-x86_64.so")
    elif system == "Linux" and machine in ("aarch64", "arm64"):
        path = os.path.join(lib_dir, "libmecab-linux-aarch64.so")
    else:
        return None
    return path if os.path.isfile(path) else None


class MecabLib:
    """MeCab running in-process through its C API, loaded with ctypes.

    Works with any Python version (no compiled extension) and needs no separate executable.
    Produces the same units as Mecab."""

    def __init__(self, lib_path: str, dic_dir: str, rc_path: str):
        try:
            lib = ctypes.CDLL(lib_path)
        except OSError as e:
            raise MecabError(f"failed to load {lib_path}: {e}")
        lib.mecab_new.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
        lib.mecab_new.restype = ctypes.c_void_p
        lib.mecab_sparse_tostr2.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
        lib.mecab_sparse_tostr2.restype = ctypes.c_char_p
        lib.mecab_strerror.argtypes = [ctypes.c_void_p]
        lib.mecab_strerror.restype = ctypes.c_char_p
        lib.mecab_destroy.argtypes = [ctypes.c_void_p]
        lib.mecab_destroy.restype = None
        self._lib = lib
        self._lock = threading.Lock()  # a MeCab instance isn't thread-safe; ctypes releases the GIL

        args = ["mecab", f"--rcfile={rc_path}", f"--dicdir={dic_dir}",
                f"--unk-feature={_UNK_FEATURE}", f"--node-format={_NODE_FORMAT}"]
        argv = (ctypes.c_char_p * len(args))(*(a.encode("utf-8") for a in args))
        self._mecab = lib.mecab_new(len(args), argv)
        if not self._mecab:
            err = lib.mecab_strerror(None)
            detail = err.decode("utf-8", "replace") if err else "no details"
            raise MecabError(f"failed to initialize MeCab with dictionary {dic_dir} ({detail})")

    def __del__(self):
        if getattr(self, "_mecab", None):
            self._lib.mecab_destroy(self._mecab)
            self._mecab = None

    def analyze(self, txt: str) -> List[ParserUnit]:
        if "\n" in txt:
            raise MecabError("line feed in text passed to analyze function")

        utf8_bytes = txt.encode("utf-8")
        with self._lock:
            out = self._lib.mecab_sparse_tostr2(self._mecab, utf8_bytes, len(utf8_bytes))
            if out is None:
                err = self._lib.mecab_strerror(self._mecab)
                raise MecabError(f"analysis failed: {err.decode('utf-8', 'replace') if err else 'unknown'}")
            output = out.decode("utf-8")
        return _units_from_output(utf8_bytes, output.splitlines())

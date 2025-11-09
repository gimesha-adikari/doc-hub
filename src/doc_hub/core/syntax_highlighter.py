import re
from typing import List, Optional, Dict, Tuple

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QColor, QTextCharFormat
from pygments.formatter import Formatter
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.token import Token, Name, Keyword, String, Comment, Number, Operator, Generic, Punctuation

try:
    from tree_sitter import Language, Parser
    _HAS_TREESITTER = True
except Exception:
    Language = None
    Parser = None
    _HAS_TREESITTER = False

TREE_SITTER_LIB = "build/my-languages.so"


class _QtFormatter(Formatter):
    def __init__(self, highlighter: QSyntaxHighlighter):
        super().__init__()
        self.highlighter = highlighter
        self.styles = {
            Token: self.create_format("#bababa"),
            Keyword: self.create_format("#9f5ee5", 75),
            Name: self.create_format("#bababa"),
            Name.Class: self.create_format("#3d8f80", 75),
            Name.Function: self.create_format("#ffc66d"),
            String: self.create_format("#6a8759"),
            Comment: self.create_format("#808080", italic=True),
            Number: self.create_format("#6897bb"),
            Operator: self.create_format("#bababa"),
            Punctuation: self.create_format("#bababa"),
            Generic.Heading: self.create_format("#bababa", 75),
        }

    @staticmethod
    def create_format(color: str, weight: int = 50, italic: bool = False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(weight)
        fmt.setFontItalic(italic)
        return fmt

    def format(self, tokensource, outfile):
        pass

    def apply_format(self, index: int, length: int, token_type):
        fmt = self.styles.get(token_type)
        if fmt is None:
            parent = getattr(token_type, "parent", None)
            while parent is not None and parent is not Token and fmt is None:
                fmt = self.styles.get(parent)
                parent = getattr(parent, "parent", None)
            fmt = fmt or self.styles[Token]
        self.highlighter.setFormat(index, length, fmt)


class TreeSitterEngine:
    def __init__(self, language_library_path: Optional[str] = None):
        self.parsers: Dict[str, Parser] = {}
        self.lang_map: Dict[str, Language] = {}
        self.library_path = language_library_path

    def load_language(self, lang_name: str, so_path: Optional[str] = None) -> Optional[Language]:
        try:
            lib = so_path or self.library_path
            if not lib:
                return None
            lang = Language(lib, lang_name)
            self.lang_map[lang_name] = lang
            parser = Parser()
            parser.set_language(lang)
            self.parsers[lang_name] = parser
            return lang
        except Exception:
            return None

    def get_parser_for_language(self, lang_name: str) -> Optional[Parser]:
        return self.parsers.get(lang_name)


def _node_range_bytes_to_char_range(text: str, start_byte: int, end_byte: int) -> Tuple[int, int]:
    b = text.encode("utf8")
    try:
        start_char = len(b[:start_byte].decode("utf8"))
        end_char = len(b[:end_byte].decode("utf8"))
    except Exception:
        start_char = len(text[:start_byte])
        end_char = len(text[:end_byte])
    return start_char, end_char


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, tree_sitter_engine: Optional[TreeSitterEngine] = None):
        super().__init__(parent)
        self.formatter = _QtFormatter(self)
        self.lexer = None
        self.search_terms: List[QRegularExpression] = []
        self.search_format = QTextCharFormat()
        self.search_format.setBackground(QColor("#ffc66d"))
        self.search_format.setForeground(QColor("#000000"))
        self.ts_engine = tree_sitter_engine if tree_sitter_engine is not None else TreeSitterEngine()
        self.language_name: Optional[str] = None
        self._ts_spans: List[Tuple[int, int, str]] = []
        self._use_treesitter = _HAS_TREESITTER

    def set_language(
        self,
        file_path: Optional[str],
        lang_hint: Optional[str] = None,
        ts_lang: Optional[str] = None,
        ts_so: Optional[str] = None,
    ):
        self.lexer = None
        self._ts_spans = []
        self.language_name = None
        if file_path is None and not lang_hint:
            self.rehighlight()
            return

        lang_name = None
        try:
            if ts_lang and self._use_treesitter:
                loaded = self.ts_engine.load_language(ts_lang, TREE_SITTER_LIB)
                if loaded:
                    lang_name = ts_lang
            if lang_name is None:
                try:
                    self.lexer = get_lexer_for_filename(file_path or "", stripnl=False)
                except Exception:
                    try:
                        text = self.document().toPlainText()
                        if text:
                            self.lexer = guess_lexer(text)
                    except Exception:
                        self.lexer = None
            self.language_name = lang_name
        except Exception:
            self.lexer = None
            self.language_name = None

        try:
            self.rebuild_treesitter_spans()
        finally:
            self.rehighlight()

    def set_search_terms(self, terms: List[str]):
        self.search_terms = [
            QRegularExpression(re.escape(term), QRegularExpression.CaseInsensitiveOption)
            for term in terms
        ]
        self.rehighlight()

    def rebuild_treesitter_spans(self):
        self._ts_spans = []
        if not self._use_treesitter or not self.language_name:
            return
        parser = self.ts_engine.get_parser_for_language(self.language_name)
        if not parser:
            return
        text = self.document().toPlainText()
        if not text:
            return
        try:
            tree = parser.parse(bytes(text, "utf8"))
            root = tree.root_node
            stack = [root]
            while stack:
                node = stack.pop()
                typ = node.type
                start, end = _node_range_bytes_to_char_range(text, node.start_byte, node.end_byte)
                self._ts_spans.append((start, end, typ))
                for child in reversed(node.children):
                    stack.append(child)
        except Exception:
            self._ts_spans = []

    def highlightBlock(self, text: str):
        block = self.currentBlock()
        block_start = block.position()
        block_end = block_start + len(text)
        applied = False

        if self._use_treesitter and self._ts_spans:
            for start, end, typ in self._ts_spans:
                if end <= block_start or start >= block_end:
                    continue
                s = max(start, block_start) - block_start
                e = min(end, block_end) - block_start
                length = max(0, e - s)
                if length <= 0:
                    continue
                token_format = self._map_treesitter_type_to_format(typ)
                if token_format:
                    self.setFormat(s, length, token_format)
                    applied = True

        if not applied and self.lexer is not None:
            try:
                tokens = self.lexer.get_tokens_unprocessed(text)
                for index, token_type, value in tokens:
                    self.formatter.apply_format(index, len(value), token_type)
            except Exception:
                pass

        if self.search_terms:
            for pattern in self.search_terms:
                it = pattern.globalMatch(text)
                while it.hasNext():
                    m = it.next()
                    length = m.capturedLength()
                    self.setFormat(m.capturedStart(), length, self.search_format)

    def _map_treesitter_type_to_format(self, node_type: str) -> Optional[QTextCharFormat]:
        t = node_type.lower()
        if "comment" in t:
            return self.formatter.create_format("#808080", italic=True)
        if "string" in t or "literal" in t:
            return self.formatter.create_format("#6a8759")
        if "function" in t or "def" in t or "method" in t:
            return self.formatter.create_format("#ffc66d")
        if "class" in t or "type" in t:
            return self.formatter.create_format("#3d8f80", 75)
        if "number" in t or "integer" in t or "float" in t:
            return self.formatter.create_format("#6897bb")
        if "keyword" in t or t in (
            "if",
            "for",
            "while",
            "return",
            "import",
            "from",
            "else",
            "try",
            "except",
            "await",
        ):
            return self.formatter.create_format("#9f5ee5", 75)
        if "identifier" in t or "name" in t:
            return self.formatter.create_format("#bababa")
        return self.formatter.create_format("#bababa")

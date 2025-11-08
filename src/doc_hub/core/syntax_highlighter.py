import re

from PySide6.QtGui import QSyntaxHighlighter,QColor, QTextCharFormat, QFont
from PySide6.QtCore import QObject, QRegularExpression

from pygments import highlight
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.formatter import Formatter
from pygments.token import (
    Token, Name, Keyword, String, Comment, Number, Operator,
    Generic, Punctuation
)

class _QtFormatter(Formatter):
    def __init__(self,highlighter:QSyntaxHighlighter):
        super().__init__()
        self.highlighter = highlighter

        self.styles = {
            Token: self.create_format("#bababa"),
            Keyword: self.create_format("#9f5ee5", QFont.Bold),
            Keyword.Constant: self.create_format("#9f5ee5", QFont.Bold),
            Keyword.Namespace: self.create_format("#9f5ee5", QFont.Bold),
            Name: self.create_format("#bababa"),
            Name.Class: self.create_format("#3d8f80", QFont.Bold),
            Name.Function: self.create_format("#ffc66d"),
            Name.Builtin.Pseudo: self.create_format("#9f5ee5", QFont.Bold),
            String: self.create_format("#6a8759"),
            String.Doc: self.create_format("#629755", italic=True),
            Comment: self.create_format("#808080", italic=True),
            Number: self.create_format("#6897bb"),
            Operator: self.create_format("#bababa"),
            Punctuation: self.create_format("#bababa"),
            Generic.Heading: self.create_format("#bababa", QFont.Bold),
            Generic.Emph: self.create_format("#bababa", italic=True),
        }

    def create_format(self,color, weight=QFont.Normal, italic=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(weight)
        fmt.setFontItalic(italic)
        return fmt

    def format(self, tokensource, outfile):
        pass

    def apply_format(self, index, length, token_type):

        fmt = self.styles.get(token_type)

        if fmt is None:
            parent = token_type.parent
            while parent is not Token and fmt is None:
                fmt = self.styles.get(parent)
                parent = parent.parent

            fmt = fmt or self.styles[Token]

        self.highlighter.setFormat(index, length, fmt)

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.formatter = _QtFormatter(self)
        self.lexer = None

        self.search_terms = []
        self.search_format = QTextCharFormat()
        self.search_format.setBackground(QColor("#ffc66d"))
        self.search_format.setForeground(QColor("#000000"))

    def set_language(self, file_path: str | None):
        if file_path is None:
            self.lexer = None
        else:
            try:
                self.lexer = get_lexer_for_filename(file_path, stripnl=False)
            except Exception:
                try:
                    text = self.document().toPlainText()
                    if text:
                        self.lexer = guess_lexer(text)
                    else:
                        self.lexer = None
                except Exception:
                    self.lexer = None

        self.rehighlight()

    def set_search_terms(self, terms:list[str]):
        self.search_terms = [
            QRegularExpression(re.escape(term), QRegularExpression.CaseInsensitiveOption)
            for term in terms
        ]
        self.rehighlight()

    def highlightBlock(self, text: str):
        if self.lexer is not None:
            try:
                tokens = self.lexer.get_tokens_unprocessed(text)
                for index, token_type, value in tokens:
                    self.formatter.apply_format(index, len(value), token_type)
            except Exception as e:
                print(f"Error during highlighting: {e}")

        if not self.search_terms:
            return

        for pattern in self.search_terms:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                length = match.capturedLength()
                self.setFormat(match.capturedStart(), length, self.search_format)
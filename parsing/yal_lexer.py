class Token:
    def __init__(self, type_: str, value: str, line: int):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line})"


class YalLexerError(Exception):
    pass


class YalLexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.tokens = []

    def tokenize(self):
        while self.pos < len(self.text):
            char = self.text[self.pos]

            if char.isspace():
                if char == '\n':
                    self.line += 1
                self.pos += 1
                continue

            if self.text.startswith("(*", self.pos):
                self._skip_comment()
                continue

            if char == '{':
                self.tokens.append(self._read_block())
                continue

            if char == '"':
                self.tokens.append(self._read_string())
                continue

            if char == "'":
                self.tokens.append(self._read_char())
                continue

            if char in "=*+?|#()[]^-":
                type_map = {
                    '=': 'EQ', '*': 'STAR', '+': 'PLUS', '?': 'OPT',
                    '|': 'PIPE', '#': 'HASH', '(': 'LPAREN', ')': 'RPAREN',
                    '[': 'LBRACKET', ']': 'RBRACKET', '^': 'CARET', '-': 'DASH'
                }
                self.tokens.append(Token(type_map[char], char, self.line))
                self.pos += 1
                continue

            if char == '_':
                self.tokens.append(Token('ANY', char, self.line))
                self.pos += 1
                continue

            if char.isalpha() or char == '_':
                ident = self._read_ident()
                if ident == "let":
                    self.tokens.append(Token("LET", ident, self.line))
                elif ident == "rule":
                    self.tokens.append(Token("RULE", ident, self.line))
                else:
                    self.tokens.append(Token("IDENT", ident, self.line))
                continue

            raise YalLexerError(f"Unexpected character {repr(char)} at line {self.line}")

        self.tokens.append(Token("EOF", "", self.line))
        return self.tokens

    def _skip_comment(self):
        depth = 0
        while self.pos < len(self.text):
            if self.text.startswith("(*", self.pos):
                depth += 1
                self.pos += 2
            elif self.text.startswith("*)", self.pos):
                depth -= 1
                self.pos += 2
                if depth == 0:
                    break
            else:
                if self.text[self.pos] == '\n':
                    self.line += 1
                self.pos += 1
        if depth > 0:
            raise YalLexerError(f"Unterminated comment starting at line {self.line}")

    def _read_block(self):
        start_line = self.line
        start_pos = self.pos
        self.pos += 1
        depth = 1
        content = []
        while self.pos < len(self.text) and depth > 0:
            c = self.text[self.pos]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            if depth > 0:
                content.append(c)
                if c == '\n':
                    self.line += 1
            self.pos += 1
            
        if depth > 0:
            raise YalLexerError(f"Unterminated block {{ ... }} starting at line {start_line}")
        return Token("BLOCK", "".join(content), start_line)

    def _read_string(self):
        start_line = self.line
        self.pos += 1
        content = []
        while self.pos < len(self.text):
            c = self.text[self.pos]
            if c == '"':
                self.pos += 1
                return Token("STRING", "".join(content), start_line)
            elif c == '\\':
                if self.pos + 1 < len(self.text):
                    content.append('\\' + self.text[self.pos+1])
                    self.pos += 2
                else:
                    raise YalLexerError("Unterminated escape sequence at end of file")
            else:
                content.append(c)
                if c == '\n':
                    self.line += 1
                self.pos += 1
        raise YalLexerError(f"Unterminated string starting at line {start_line}")

    def _read_char(self):
        start_line = self.line
        self.pos += 1
        content = ""
        if self.pos < len(self.text) and self.text[self.pos] == '\\':
            content = '\\' + self.text[self.pos+1]
            self.pos += 2
        elif self.pos < len(self.text):
            content = self.text[self.pos]
            self.pos += 1

        if self.pos < len(self.text) and self.text[self.pos] == "'":
            self.pos += 1
            return Token("CHAR", content, start_line)
        raise YalLexerError(f"Invalid char literal starting at line {start_line}")

    def _read_ident(self):
        start_pos = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return self.text[start_pos:self.pos]

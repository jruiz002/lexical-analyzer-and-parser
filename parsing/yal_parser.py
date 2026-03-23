from core.ast_nodes import *
from parsing.yal_lexer import Token, YalLexer, YalLexerError

class YalParserError(Exception):
    pass

# Parser para archivos .yal, convierte la lista de tokens en un AST (YalDocument)
class YalParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # Retorna el token actual sin avanzar, o EOF si ya se terminaron los tokens
    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token("EOF", "", -1)

    def advance(self):
        self.pos += 1

    # Avanza si el token actual es del tipo esperado, sino retorna False
    def match(self, token_type: str) -> bool:
        if self.current().type == token_type:
            self.advance()
            return True
        return False

    # Consume el token actual si es del tipo esperado, sino lanza error
    def expect(self, token_type: str) -> Token:
        t = self.current()
        if t.type == token_type:
            self.advance()
            return t
        raise YalParserError(f"Expected {token_type}, but got {t.type} '{t.value}' at line {t.line}")

    # Parsea el documento completo y construye el YalDocument con lets, reglas, header y trailer
    def parse(self) -> YalDocument:
        doc = YalDocument()

        if self.current().type == "BLOCK":
            doc.header = self.current().value
            self.advance()

        while self.current().type == "LET":
            self.advance()
            ident_idx = self.expect("IDENT").value
            self.expect("EQ")
            regex = self.parse_regex()
            doc.lets.append(LetDecl(ident_idx, regex))

        self.expect("RULE")
        doc.entrypoint_name = self.expect("IDENT").value
        while self.current().type != "EQ":
            t = self.current()
            if t.type in ("LBRACKET", "RBRACKET", "IDENT", "BLOCK"):
                if t.type == "IDENT":
                    doc.entrypoint_args.append(t.value)
                self.advance()
            else:
                break
        self.expect("EQ")

        doc.rules.append(self.parse_rule())
        while self.match("PIPE"):
             doc.rules.append(self.parse_rule())

        if self.current().type == "BLOCK":
             doc.trailer = self.current().value
             self.advance()

        if self.current().type != "EOF":
            raise YalParserError(f"Unexpected token {self.current()} at end of file")

        return doc

    # Parsea una regla individual: su regex y la acción opcional entre llaves
    def parse_rule(self) -> RuleDecl:
        regex = self.parse_regex()
        action = None
        if self.current().type == "BLOCK":
            action = self.current().value
            self.advance()
        return RuleDecl(regex, action)

    def parse_regex(self) -> RegexNode:
        return self.parse_union()

    # Parsea uniones (a | b), con menor precedencia que la concatenación
    def parse_union(self) -> RegexNode:
        node = self.parse_concat()
        while self.match("PIPE"):
            right = self.parse_concat()
            node = UnionNode(node, right)
        return node

    # Parsea concatenaciones implícitas entre expresiones adyacentes
    def parse_concat(self) -> RegexNode:
        node = self.parse_postfix()
        while self.current().type in ("ANY", "IDENT", "CHAR", "STRING", "LBRACKET", "LPAREN"):
            right = self.parse_postfix()
            node = ConcatNode(node, right)
        return node

    # Parsea los operadores postfijos *, + y ?
    def parse_postfix(self) -> RegexNode:
        node = self.parse_diff()
        while self.current().type in ("STAR", "PLUS", "OPT"):
            op = self.current()
            self.advance()
            if op.type == "STAR":
                node = StarNode(node)
            elif op.type == "PLUS":
                node = PlusNode(node)
            elif op.type == "OPT":
                node = OptionNode(node)
        return node

    # Parsea la diferencia de conjuntos con el operador #
    def parse_diff(self) -> RegexNode:
        node = self.parse_primary()
        while self.match("HASH"):
            right = self.parse_primary()
            node = DiffNode(node, right)
        return node

    # Parsea los elementos primarios: caracteres, strings, idents, grupos y conjuntos
    def parse_primary(self) -> RegexNode:
        t = self.current()
        if t.type == "ANY":
            self.advance()
            return AnyNode()
        elif t.type == "IDENT":
            self.advance()
            return IdentNode(t.value)
        elif t.type == "CHAR":
            self.advance()
            return CharNode(self._unescape(t.value))
        elif t.type == "STRING":
            self.advance()
            return StringNode(self._unescape_string(t.value))
        elif t.type == "LPAREN":
            self.advance()
            node = self.parse_regex()
            self.expect("RPAREN")
            return node
        elif t.type == "LBRACKET":
            self.advance()
            return self.parse_set()
        
        raise YalParserError(f"Unexpected token {t} while parsing regex")

    # Parsea un conjunto de caracteres [ ... ], con soporte para rangos y negación
    def parse_set(self) -> RegexNode:
        negated = self.match("CARET")
        elements = set()
        
        while self.current().type != "RBRACKET":
            t = self.current()
            if t.type == "STRING":
                for ch in self._unescape_string(t.value):
                    elements.add(ch)
                self.advance()
            elif t.type == "CHAR":
                start_char_unescaped = self._unescape(t.value)
                self.advance()
                if self.match("DASH"):
                    end_char_unescaped = self._unescape(self.expect("CHAR").value)
                    # calcula el rango de caracteres entre los dos extremos
                    start_ascii = ord(start_char_unescaped)
                    end_ascii = ord(end_char_unescaped)
                    for i in range(start_ascii, end_ascii + 1):
                        elements.add(chr(i))
                else:
                    elements.add(start_char_unescaped)
            else:
                raise YalParserError(f"Invalid item {t} in character set")
        
        self.expect("RBRACKET")
        return SetNode(elements, negated)

    # Convierte una secuencia de escape de un carácter a su valor real
    def _unescape(self, item: str) -> str:
        if len(item) == 2 and item[0] == '\\':
            escapes = {'n': '\n', 't': '\t', 'r': '\r', 's': ' '}
            return escapes.get(item[1], item[1])
        return item[0]

    # Procesa todas las secuencias de escape dentro de un string completo
    def _unescape_string(self, item: str) -> str:
        idx = 0
        res = []
        while idx < len(item):
            if item[idx] == '\\' and idx + 1 < len(item):
                res.append(self._unescape('\\' + item[idx+1]))
                idx += 2
            else:
                res.append(item[idx])
                idx += 1
        return "".join(res)

    # Retorna el valor ASCII de un carácter, aplicando unescape si hace falta
    def _char_value(self, item: str) -> int:
        return ord(self._unescape(item))

# Lee un archivo .yal, lo tokeniza y retorna el YalDocument parseado
def parse_yal(file_path: str) -> YalDocument:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lexer = YalLexer(content)
    tokens = lexer.tokenize()
    parser = YalParser(tokens)
    return parser.parse()
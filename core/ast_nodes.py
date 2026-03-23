from typing import List, Optional, Set, Any

# Clase base para todos los nodos del AST del regex, tiene las propiedades para la construcción directa del DFA.
class RegexNode:
    def __init__(self):
        # propiedades para la construcción directa del DFA
        self.nullable: Optional[bool] = None
        self.firstpos: Set[int] = set()
        self.lastpos: Set[int] = set()
    
    # Calcula nullable, firstpos y lastpos de forma recursiva.
    def calculate_positions(self) -> None:
        pass

    # Imprime el árbol del nodo con su estructura de hijos.
    def print_tree(self, prefix: str = ""):
        print(f"{prefix}{self.__class__.__name__}")
        if hasattr(self, 'value'):
            print(f"{prefix}  └─ Value: {repr(self.value)}")
        elif hasattr(self, 'char'):
            print(f"{prefix}  └─ Char: {repr(self.char)}")
        elif hasattr(self, 'elements'):
            print(f"{prefix}  └─ Elements: {list(self.elements)}")
        elif hasattr(self, 'name'):
            print(f"{prefix}  └─ Ident: {self.name}")
            
        if hasattr(self, 'left'):
            self.left.print_tree(prefix + "  │ ")
        if hasattr(self, 'right'):
            self.right.print_tree(prefix + "  └ ")
            
        if hasattr(self, 'child'):
            self.child.print_tree(prefix + "  └ ")

# Clase base para nodos hoja que consumen un símbolo, como Char, Any o Set.
class LeafNode(RegexNode):
    def __init__(self):
        super().__init__()
        self.position: Optional[int] = None

# Nodo que representa un carácter literal o secuencia de escape.
class CharNode(LeafNode):
    def __init__(self, char: str):
        super().__init__()
        self.char = char

    def __repr__(self):
        return f"Char('{self.char}')"

# Nodo que representa una cadena de caracteres completa.
class StringNode(RegexNode):
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"String(\"{self.value}\")"

# Nodo que representa el comodín '_', hace match con cualquier carácter.
class AnyNode(LeafNode):
    def __repr__(self):
        return "Any()"

# Nodo que representa un conjunto de caracteres, puede ser negado con [^...].
class SetNode(LeafNode):
    def __init__(self, elements: Set[str], negated: bool = False):
        super().__init__()
        self.elements = elements
        self.negated = negated

    def __repr__(self):
        prefix = "^" if self.negated else ""
        return f"Set([{prefix}...])"

# Nodo que referencia una definición 'let' por nombre.
class IdentNode(RegexNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __repr__(self):
        return f"Ident({self.name})"

# Operadores del regex

# Nodo que representa la concatenación de dos expresiones.
class ConcatNode(RegexNode):
    def __init__(self, left: RegexNode, right: RegexNode):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Concat({self.left}, {self.right})"

# Nodo que representa la unión (alternativa) entre dos expresiones.
class UnionNode(RegexNode):
    def __init__(self, left: RegexNode, right: RegexNode):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Union({self.left}, {self.right})"

# Nodo que representa la diferencia entre dos conjuntos de caracteres (regexp1 # regexp2).
class DiffNode(RegexNode):
    def __init__(self, left: RegexNode, right: RegexNode):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Diff({self.left}, {self.right})"

# Nodo para el operador '*', cero o más repeticiones.
class StarNode(RegexNode):
    def __init__(self, child: RegexNode):
        super().__init__()
        self.child = child

    def __repr__(self):
        return f"Star({self.child})"

# Nodo para el operador '+', una o más repeticiones.
class PlusNode(RegexNode):
    def __init__(self, child: RegexNode):
        super().__init__()
        self.child = child

    def __repr__(self):
        return f"Plus({self.child})"

# Nodo para el operador '?', cero o una ocurrencia.
class OptionNode(RegexNode):
    def __init__(self, child: RegexNode):
        super().__init__()
        self.child = child

    def __repr__(self):
        return f"Option({self.child})"

# Estructuras de alto nivel

# Representa una declaración 'let' que le asigna un nombre a un regex.
class LetDecl:
    def __init__(self, name: str, regex: RegexNode):
        self.name = name
        self.regex = regex

    def __repr__(self):
        return f"Let({self.name} = {self.regex})"

# Representa una regla del lexer: un regex y la acción que ejecuta al hacer match.
class RuleDecl:
    def __init__(self, regex: RegexNode, action: Optional[str]):
        self.regex = regex
        self.action = action

    def __repr__(self):
        return f"Rule({self.regex} => {self.action})"

# Representa el documento .yal completo con sus lets, reglas, header y trailer.
class YalDocument:
    def __init__(self):
        self.header: Optional[str] = None
        self.trailer: Optional[str] = None
        self.lets: List[LetDecl] = []
        self.entrypoint_name: str = "entrypoint"
        self.entrypoint_args: List[str] = []
        self.rules: List[RuleDecl] = []

    # Imprime el árbol de todas las reglas del documento.
    def print_tree(self):
        print("AST - Entrypoint Rules:")
        for idx, rule in enumerate(self.rules):
            print(f"\nRule {idx}:")
            rule.regex.print_tree("  ")

    def __repr__(self):
        return f"YalDocument(lets={len(self.lets)}, rules={len(self.rules)})"

# Nodo hoja especial que se agrega al final de un regex de regla para marcar aceptación.
class AcceptNode(LeafNode):
    def __init__(self, rule_index: int, action: Optional[str]):
        super().__init__()
        self.rule_index = rule_index
        self.action = action

    def __repr__(self):
        return f"Accept(rule={self.rule_index})"
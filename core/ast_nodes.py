from typing import List, Optional, Set, Any

class RegexNode:
    """Base class for all Regex AST nodes."""
    def __init__(self):
        # Properties for Direct DFA construction
        self.nullable: Optional[bool] = None
        self.firstpos: Set[int] = set()
        self.lastpos: Set[int] = set()
    
    def calculate_positions(self) -> None:
        """Calculate nullable, firstpos, and lastpos recursively."""
        pass

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

class LeafNode(RegexNode):
    """Base class for leaf nodes that consume a symbol (Char, Any, Set)."""
    def __init__(self):
        super().__init__()
        self.position: Optional[int] = None

class CharNode(LeafNode):
    """Matches a single character or escape sequence."""
    def __init__(self, char: str):
        super().__init__()
        self.char = char

    def __repr__(self):
        return f"Char('{self.char}')"

class StringNode(RegexNode):
    """Matches a sequence of characters."""
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"String(\"{self.value}\")"

class AnyNode(LeafNode):
    """Matches any single character (represented by '_' in yal)."""
    def __repr__(self):
        return "Any()"

class SetNode(LeafNode):
    """Matches any character in a set (e.g. ['a'-'z' 'A'-'Z'])."""
    def __init__(self, elements: Set[str], negated: bool = False):
        super().__init__()
        self.elements = elements
        self.negated = negated  # for [^...]

    def __repr__(self):
        prefix = "^" if self.negated else ""
        return f"Set([{prefix}...])"

class IdentNode(RegexNode):
    """Reference to a 'let' definition."""
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __repr__(self):
        return f"Ident({self.name})"

# Regex Operators

class ConcatNode(RegexNode):
    def __init__(self, left: RegexNode, right: RegexNode):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Concat({self.left}, {self.right})"

class UnionNode(RegexNode):
    def __init__(self, left: RegexNode, right: RegexNode):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Union({self.left}, {self.right})"

class DiffNode(RegexNode):
    """Difference of two sets (regexp1 # regexp2)."""
    def __init__(self, left: RegexNode, right: RegexNode):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return f"Diff({self.left}, {self.right})"

class StarNode(RegexNode):
    def __init__(self, child: RegexNode):
        super().__init__()
        self.child = child

    def __repr__(self):
        return f"Star({self.child})"

class PlusNode(RegexNode):
    def __init__(self, child: RegexNode):
        super().__init__()
        self.child = child

    def __repr__(self):
        return f"Plus({self.child})"

class OptionNode(RegexNode):
    def __init__(self, child: RegexNode):
        super().__init__()
        self.child = child

    def __repr__(self):
        return f"Option({self.child})"

# Top level structures

class LetDecl:
    def __init__(self, name: str, regex: RegexNode):
        self.name = name
        self.regex = regex

    def __repr__(self):
        return f"Let({self.name} = {self.regex})"

class RuleDecl:
    def __init__(self, regex: RegexNode, action: Optional[str]):
        self.regex = regex
        self.action = action

    def __repr__(self):
        return f"Rule({self.regex} => {self.action})"

class YalDocument:
    def __init__(self):
        self.header: Optional[str] = None
        self.trailer: Optional[str] = None
        self.lets: List[LetDecl] = []
        self.entrypoint_name: str = "entrypoint"
        self.entrypoint_args: List[str] = []
        self.rules: List[RuleDecl] = []

    def print_tree(self):
        """Prints a visual representation of all rules."""
        print("AST - Entrypoint Rules:")
        for idx, rule in enumerate(self.rules):
            print(f"\nRule {idx}:")
            rule.regex.print_tree("  ")

    def __repr__(self):
        return f"YalDocument(lets={len(self.lets)}, rules={len(self.rules)})"

class AcceptNode(LeafNode):
    """Special leaf node appended at the end of a rule regex to indicate acceptance."""
    def __init__(self, rule_index: int, action: Optional[str]):
        super().__init__()
        self.rule_index = rule_index
        self.action = action

    def __repr__(self):
        return f"Accept(rule={self.rule_index})"

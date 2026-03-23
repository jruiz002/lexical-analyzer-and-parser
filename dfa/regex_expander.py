from core.ast_nodes import *

class ExpansionError(Exception):
    pass

# Copia y expande recursivamente un nodo de regex, resolviendo los IdentNodes con el entorno dado
def expand_regex(node: RegexNode, env: dict) -> RegexNode:
    if isinstance(node, AnyNode):
        return AnyNode()
    elif isinstance(node, CharNode):
        return CharNode(node.char)
    elif isinstance(node, StringNode):
        return StringNode(node.value)
    elif isinstance(node, SetNode):
        # hay que hacer una copia nueva del conjunto
        return SetNode(set(node.elements), node.negated)
    elif isinstance(node, IdentNode):
        if node.name == "eof":
            return CharNode(chr(256))
        if node.name not in env:
            raise ExpansionError(f"Undefined identifier '{node.name}' used in regex")
        # se expande recursivamente por si el env tiene sus propios idents, igual se necesita copiar
        return expand_regex(env[node.name], env)
    
    # Operadores
    elif isinstance(node, ConcatNode):
        return ConcatNode(expand_regex(node.left, env), expand_regex(node.right, env))
    elif isinstance(node, UnionNode):
        return UnionNode(expand_regex(node.left, env), expand_regex(node.right, env))
    elif isinstance(node, DiffNode):
        return DiffNode(expand_regex(node.left, env), expand_regex(node.right, env))
    elif isinstance(node, StarNode):
        return StarNode(expand_regex(node.child, env))
    elif isinstance(node, PlusNode):
        return PlusNode(expand_regex(node.child, env))
    elif isinstance(node, OptionNode):
        return OptionNode(expand_regex(node.child, env))
    
    raise ExpansionError(f"Unknown node type during expansion: {type(node)}")

# Expande todas las reglas de un YalDocument y retorna la lista de RuleDecls con los regex ya resueltos
def expand_document(doc: YalDocument) -> List[RuleDecl]:
    env = {}
    # se expanden los lets en orden para que cada uno pueda usar los anteriores
    for let_decl in doc.lets:
        expanded_regex = expand_regex(let_decl.regex, env)
        env[let_decl.name] = expanded_regex

    expanded_rules = []
    for rule in doc.rules:
        expanded_rule_regex = expand_regex(rule.regex, env)
        expanded_rules.append(RuleDecl(expanded_rule_regex, rule.action))

    return expanded_rules
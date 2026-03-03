from core.ast_nodes import *

class ExpansionError(Exception):
    pass

def expand_regex(node: RegexNode, env: dict) -> RegexNode:
    """Recursively deep copies and expands RegexNodes resolving IdentNodes using env."""
    if isinstance(node, AnyNode):
        return AnyNode()
    elif isinstance(node, CharNode):
        return CharNode(node.char)
    elif isinstance(node, StringNode):
        return StringNode(node.value)
    elif isinstance(node, SetNode):
        # We need a new copy of the set
        return SetNode(set(node.elements), node.negated)
    elif isinstance(node, IdentNode):
        if node.name == "eof":
            return CharNode(chr(256))
        if node.name not in env:
            raise ExpansionError(f"Undefined identifier '{node.name}' used in regex")
        # Recursively expand in case the env stored regex has its own idents (though we expand them sequentially so they shouldn't, but copy is needed!)
        return expand_regex(env[node.name], env)
    
    # Operators
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

def expand_document(doc: YalDocument) -> List[RuleDecl]:
    """
    Expands all rules in a YalDocument.
    Returns a list of RuleDecls with fully expanded regexes.
    """
    env = {}
    # Expand lets sequentially
    for let_decl in doc.lets:
        expanded_regex = expand_regex(let_decl.regex, env)
        env[let_decl.name] = expanded_regex

    expanded_rules = []
    for rule in doc.rules:
        expanded_rule_regex = expand_regex(rule.regex, env)
        expanded_rules.append(RuleDecl(expanded_rule_regex, rule.action))

    return expanded_rules

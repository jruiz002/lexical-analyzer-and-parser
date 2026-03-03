from core.ast_nodes import *
from core.automata import DFA, DFAState

class DirectDFABuilder:
    def __init__(self):
        self.pos_count = 1
        self.pos_to_node = {}
        self.followpos = {}
        self.alphabet = set()

    def preprocess(self, node: RegexNode) -> RegexNode:
        """Transforms StringNode into Concats, and DiffNode into SetNode."""
        if isinstance(node, StringNode):
            if len(node.value) == 0:
                raise ValueError("Empty string not supported natively without EpsilonNode")
            if len(node.value) == 1:
                return CharNode(node.value[0])
            # Build right-heavy Concat tree
            current = CharNode(node.value[-1])
            for char in reversed(node.value[:-1]):
                current = ConcatNode(CharNode(char), current)
            return current
            
        elif isinstance(node, DiffNode):
            left = self.preprocess(node.left)
            right = self.preprocess(node.right)
            if isinstance(left, SetNode) and isinstance(right, SetNode):
                # evaluate set difference
                new_elements = left.elements - right.elements
                return SetNode(new_elements, negated=False) # Negated logic complicates this, assume simple
            else:
                raise ValueError("Diff operator (#) only supported between Character Sets")

        elif isinstance(node, ConcatNode):
            return ConcatNode(self.preprocess(node.left), self.preprocess(node.right))
        elif isinstance(node, UnionNode):
            return UnionNode(self.preprocess(node.left), self.preprocess(node.right))
        elif isinstance(node, StarNode):
            return StarNode(self.preprocess(node.child))
        elif isinstance(node, PlusNode):
            return PlusNode(self.preprocess(node.child))
        elif isinstance(node, OptionNode):
            return OptionNode(self.preprocess(node.child))
            
        return node
        
    def gather_alphabet(self, node: RegexNode):
        if isinstance(node, CharNode):
            self.alphabet.add(node.char)
        elif isinstance(node, SetNode):
            for c in node.elements:
                self.alphabet.add(c)
        elif isinstance(node, ConcatNode) or isinstance(node, UnionNode):
            self.gather_alphabet(node.left)
            self.gather_alphabet(node.right)
        elif isinstance(node, StarNode) or isinstance(node, PlusNode) or isinstance(node, OptionNode):
            self.gather_alphabet(node.child)

    def calculate_positions(self, node: RegexNode):
        if isinstance(node, LeafNode):
            node.position = self.pos_count
            self.pos_to_node[self.pos_count] = node
            self.followpos[self.pos_count] = set()
            self.pos_count += 1
            node.nullable = False
            node.firstpos = {node.position}
            node.lastpos = {node.position}

        elif isinstance(node, ConcatNode):
            self.calculate_positions(node.left)
            self.calculate_positions(node.right)
            node.nullable = node.left.nullable and node.right.nullable
            node.firstpos = set(node.left.firstpos)
            if node.left.nullable:
                node.firstpos.update(node.right.firstpos)
            node.lastpos = set(node.right.lastpos)
            if node.right.nullable:
                node.lastpos.update(node.left.lastpos)
                
            for i in node.left.lastpos:
                self.followpos[i].update(node.right.firstpos)

        elif isinstance(node, UnionNode):
            self.calculate_positions(node.left)
            self.calculate_positions(node.right)
            node.nullable = node.left.nullable or node.right.nullable
            node.firstpos = node.left.firstpos | node.right.firstpos
            node.lastpos = node.left.lastpos | node.right.lastpos

        elif isinstance(node, StarNode):
            self.calculate_positions(node.child)
            node.nullable = True
            node.firstpos = set(node.child.firstpos)
            node.lastpos = set(node.child.lastpos)
            for i in node.lastpos:
                self.followpos[i].update(node.firstpos)

        elif isinstance(node, PlusNode):
            self.calculate_positions(node.child)
            node.nullable = node.child.nullable
            node.firstpos = set(node.child.firstpos)
            node.lastpos = set(node.child.lastpos)
            for i in node.lastpos:
                self.followpos[i].update(node.firstpos)

        elif isinstance(node, OptionNode):
            self.calculate_positions(node.child)
            node.nullable = True
            node.firstpos = set(node.child.firstpos)
            node.lastpos = set(node.child.lastpos)
            
    def match_symbol(self, pos: int, symbol: str) -> bool:
        """Checks if the leaf node at pos matches the given symbol."""
        node = self.pos_to_node[pos]
        if isinstance(node, AcceptNode):
            return False
        if isinstance(node, AnyNode):
            return True
        if isinstance(node, CharNode):
            return node.char == symbol
        if isinstance(node, SetNode):
            return (symbol not in node.elements) if node.negated else (symbol in node.elements)
        return False

    def build(self, rules: List[RuleDecl]) -> DFA:
        # 1. Expand properties & preprocess rules
        processed_rules = []
        for i, rule in enumerate(rules):
            clean_regex = self.preprocess(rule.regex)
            # Append AcceptNode with priority i
            concat = ConcatNode(clean_regex, AcceptNode(i, rule.action))
            processed_rules.append(concat)
            
        # 2. Union all processed rules into a single syntax tree
        root = processed_rules[0]
        for pr in processed_rules[1:]:
            root = UnionNode(root, pr)
            
        # 3. Gather alphabet (including 0-255 for robust evaluation against ANY)
        self.gather_alphabet(root)
        # Add basic ASCII printables and typical whitespace just in case ANY doesn't get tested otherwise
        for c in " \t\n\r" + "".join(chr(i) for i in range(32, 127)):
            self.alphabet.add(c)
            
        # 4. Calculate nullable, firstpos, lastpos, followpos
        self.calculate_positions(root)
        
        # 5. Build DFA
        start_positions = frozenset(root.firstpos)
        
        def is_accepting(positions: frozenset):
            rule_indices = []
            for pos in positions:
                node = self.pos_to_node[pos]
                if isinstance(node, AcceptNode):
                    rule_indices.append((node.rule_index, node.action))
            if not rule_indices:
                return False, None
            # Lowest index has highest priority
            rule_indices.sort(key=lambda x: x[0])
            return True, rule_indices[0] # Return Top priority rule index and action
            
        acc, top_rule = is_accepting(start_positions)
        start_state = DFAState(start_positions, is_accepting=acc, tag=top_rule)
        
        states = {start_positions: start_state}
        unmarked = [start_state]
        accept_states = set()
        if start_state.is_accepting:
            accept_states.add(start_state)
            
        while unmarked:
            s = unmarked.pop(0)
            
            # For every symbol in alphabet, compute U
            for a in self.alphabet:
                u = set()
                for pos in s.nfa_states:
                    if self.match_symbol(pos, a):
                        u.update(self.followpos[pos])
                if not u:
                    continue
                    
                u_frozen = frozenset(u)
                if u_frozen not in states:
                    new_acc, new_top_rule = is_accepting(u_frozen)
                    new_state = DFAState(u_frozen, is_accepting=new_acc, tag=new_top_rule)
                    states[u_frozen] = new_state
                    unmarked.append(new_state)
                    if new_state.is_accepting:
                        accept_states.add(new_state)
                        
                s.add_transition(a, states[u_frozen])
                
        return DFA(start_state, accept_states)

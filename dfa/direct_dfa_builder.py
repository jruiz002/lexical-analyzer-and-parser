from core.ast_nodes import *
from core.automata import DFA, DFAState

# Construye un DFA directamente desde el AST del regex sin pasar por un NFA
class DirectDFABuilder:
    def __init__(self):
        self.pos_count = 1
        self.pos_to_node = {}
        self.followpos = {}
        self.alphabet = set()

    # Convierte StringNodes en concatenaciones de CharNodes y DiffNodes en SetNodes
    def preprocess(self, node: RegexNode) -> RegexNode:
        if isinstance(node, StringNode):
            if len(node.value) == 0:
                raise ValueError("Empty string not supported natively without EpsilonNode")
            if len(node.value) == 1:
                return CharNode(node.value[0])
            # construye el árbol de concat cargado a la derecha

            current = CharNode(node.value[-1])
            for char in reversed(node.value[:-1]):
                current = ConcatNode(CharNode(char), current)
            return current
            
        elif isinstance(node, DiffNode):
            left = self.preprocess(node.left)
            right = self.preprocess(node.right)
            if isinstance(left, SetNode) and isinstance(right, SetNode):
                # calcula la diferencia de conjuntos directamente
                new_elements = left.elements - right.elements
                return SetNode(new_elements, negated=False)
            
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

    # Recorre el árbol y recolecta todos los símbolos que aparecen en el regex
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

    # Calcula nullable, firstpos, lastpos y followpos para cada nodo del árbol
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

    # Verifica si el nodo hoja en la posición dada hace match con el símbolo recibido
    def match_symbol(self, pos: int, symbol: str) -> bool:
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

    # Construye el DFA a partir de la lista de reglas, ejecuta todos los pasos del algoritmo
    def build(self, rules: List[RuleDecl]) -> DFA:
        # 1. Preprocesar las reglas y agregarles el AcceptNode con su prioridad
        processed_rules = []
        for i, rule in enumerate(rules):
            clean_regex = self.preprocess(rule.regex)
            concat = ConcatNode(clean_regex, AcceptNode(i, rule.action))
            processed_rules.append(concat)
            
        # 2. Unir todas las reglas en un solo árbol con Union
        root = processed_rules[0]
        for pr in processed_rules[1:]:
            root = UnionNode(root, pr)
            
        # 3. Recolectar el alfabeto, se agregan ASCII básicos por si ANY no se evalúa de otra forma
        self.gather_alphabet(root)
        for c in " \t\n\r" + "".join(chr(i) for i in range(32, 127)):
            self.alphabet.add(c)
            
        # 4. Calcular nullable, firstpos, lastpos y followpos
        self.calculate_positions(root)
        
        # 5. Construir el DFA por subconjuntos
        start_positions = frozenset(root.firstpos)
        
        # retorna si el conjunto de posiciones es de aceptación y cuál regla tiene mayor prioridad
        def is_accepting(positions: frozenset):
            rule_indices = []
            for pos in positions:
                node = self.pos_to_node[pos]
                if isinstance(node, AcceptNode):
                    rule_indices.append((node.rule_index, node.action))
            if not rule_indices:
                return False, None
            # el índice más bajo tiene mayor prioridad
            rule_indices.sort(key=lambda x: x[0])
            return True, rule_indices[0]
            
        acc, top_rule = is_accepting(start_positions)
        start_state = DFAState(start_positions, is_accepting=acc, tag=top_rule)
        
        states = {start_positions: start_state}
        unmarked = [start_state]
        accept_states = set()
        if start_state.is_accepting:
            accept_states.add(start_state)
            
        while unmarked:
            s = unmarked.pop(0)
            
            # para cada símbolo del alfabeto se calcula el conjunto U de followpos
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
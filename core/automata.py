import itertools
from typing import Dict, Set, Optional, Any

# Representa un estado en un NFA o DFA, guarda sus transiciones y si es de aceptación.
class State:
    _id_counter = itertools.count()

    def __init__(self, is_accepting: bool = False, tag: Optional[Any] = None):
        self.id = next(self._id_counter)
        self.is_accepting = is_accepting
        # tag guarda qué regla del regex acepta este estado
        self.tag = tag
        # para NFA: símbolo -> conjunto de estados; para DFA: símbolo -> un estado
        self.transitions: Dict[str, Set['State']] = {}
        self.epsilon_transitions: Set['State'] = set()

    # Agrega una transición con símbolo hacia otro estado.
    def add_transition(self, symbol: str, state: 'State'):
        if symbol not in self.transitions:
            self.transitions[symbol] = set()
        self.transitions[symbol].add(state)

    # Agrega una transición épsilon hacia otro estado.
    def add_epsilon_transition(self, state: 'State'):
        self.epsilon_transitions.add(state)

    def __repr__(self):
        acc = "*" if self.is_accepting else ""
        return f"q{self.id}{acc}"


# Representa un Autómata Finito No Determinista con su estado inicial y estados de aceptación.
class NFA:
    def __init__(self, start_state: State, accept_states: Set[State]):
        self.start_state = start_state
        self.accept_states = accept_states

    # Retorna todos los estados del NFA haciendo un recorrido BFS/DFS.
    def get_states(self) -> Set[State]:
        visited = set()
        stack = [self.start_state]
        while stack:
            state = stack.pop()
            if state not in visited:
                visited.add(state)
                for next_state in state.epsilon_transitions:
                    stack.append(next_state)
                for next_states in state.transitions.values():
                    for next_state in next_states:
                        stack.append(next_state)
        return visited


# Estado para el DFA, guarda el conjunto de estados del NFA que representa.
class DFAState:
    _id_counter = itertools.count()

    def __init__(self, nfa_states: frozenset = None, is_accepting: bool = False, tag: Optional[Any] = None):
        self.id = next(self._id_counter)
        # conjunto de estados NFA (o posiciones del AST) que este estado DFA representa
        self.nfa_states = nfa_states if nfa_states is not None else frozenset()
        self.is_accepting = is_accepting
        self.tag = tag
        self.transitions: Dict[str, 'DFAState'] = {}

    # Agrega una transición determinista con símbolo hacia otro estado DFA.
    def add_transition(self, symbol: str, state: 'DFAState'):
        self.transitions[symbol] = state

    def __repr__(self):
        acc = "*" if self.is_accepting else ""
        return f"D{self.id}{acc}"


# Representa un Autómata Finito Determinista con su estado inicial y estados de aceptación.
class DFA:
    def __init__(self, start_state: DFAState, accept_states: Set[DFAState]):
        self.start_state = start_state
        self.accept_states = accept_states

    # Retorna todos los estados del DFA recorriéndolos desde el estado inicial.
    def get_states(self) -> Set[DFAState]:
        visited = set()
        stack = [self.start_state]
        while stack:
            state = stack.pop()
            if state not in visited:
                visited.add(state)
                for next_state in state.transitions.values():
                    stack.append(next_state)
        return visited
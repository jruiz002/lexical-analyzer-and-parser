import itertools
from typing import Dict, Set, Optional, Any

class State:
    """Represents a state in an NFA or DFA."""
    _id_counter = itertools.count()

    def __init__(self, is_accepting: bool = False, tag: Optional[Any] = None):
        self.id = next(self._id_counter)
        self.is_accepting = is_accepting
        # tag can store information like what regex rule this accepting state matches
        self.tag = tag
        # transitions: symbol -> set of States (for NFA) or single State (for DFA)
        self.transitions: Dict[str, Set['State']] = {}
        # epsilon transitions (for NFA)
        self.epsilon_transitions: Set['State'] = set()

    def add_transition(self, symbol: str, state: 'State'):
        if symbol not in self.transitions:
            self.transitions[symbol] = set()
        self.transitions[symbol].add(state)

    def add_epsilon_transition(self, state: 'State'):
        self.epsilon_transitions.add(state)

    def __repr__(self):
        acc = "*" if self.is_accepting else ""
        return f"q{self.id}{acc}"


class NFA:
    """Represents a Nondeterministic Finite Automaton."""
    def __init__(self, start_state: State, accept_states: Set[State]):
        self.start_state = start_state
        self.accept_states = accept_states

    def get_states(self) -> Set[State]:
        """Returns all states in the NFA via BFS/DFS."""
        visited = set()
        stack = [self.start_state]
        while stack:
            state = stack.pop()
            if state not in visited:
                visited.add(state)
                # target states from epsilon
                for next_state in state.epsilon_transitions:
                    stack.append(next_state)
                # target states from symbols
                for next_states in state.transitions.values():
                    for next_state in next_states:
                        stack.append(next_state)
        return visited


class DFAState:
    """Represents a state specifically tailored for a DFA."""
    _id_counter = itertools.count()

    def __init__(self, nfa_states: frozenset = None, is_accepting: bool = False, tag: Optional[Any] = None):
        self.id = next(self._id_counter)
        # the set of NFA states (or AST positions for direct DFA) this DFA state represents
        self.nfa_states = nfa_states if nfa_states is not None else frozenset()
        self.is_accepting = is_accepting
        self.tag = tag
        self.transitions: Dict[str, 'DFAState'] = {}

    def add_transition(self, symbol: str, state: 'DFAState'):
        self.transitions[symbol] = state

    def __repr__(self):
        acc = "*" if self.is_accepting else ""
        return f"D{self.id}{acc}"


class DFA:
    """Represents a Deterministic Finite Automaton."""
    def __init__(self, start_state: DFAState, accept_states: Set[DFAState]):
        self.start_state = start_state
        self.accept_states = accept_states

    def get_states(self) -> Set[DFAState]:
        """Returns all states in the DFA."""
        visited = set()
        stack = [self.start_state]
        while stack:
            state = stack.pop()
            if state not in visited:
                visited.add(state)
                for next_state in state.transitions.values():
                    stack.append(next_state)
        return visited

from core.automata import DFA, DFAState

# Minimiza un DFA usando el algoritmo de Hopcroft, retorna un DFA nuevo con menos estados
def minimize_dfa(dfa: DFA) -> DFA:
    states = dfa.get_states()
    alphabet = set()
    for s in states:
        alphabet.update(s.transitions.keys())

    # 1. Particiones iniciales
    partitions_dict = {}
    for s in states:
        if s.is_accepting:
            key = s.tag
        else:
            key = None
            
        if key not in partitions_dict:
            partitions_dict[key] = set()
        partitions_dict[key].add(s)

    P = list(partitions_dict.values())
    W = list(partitions_dict.values())

    # 2. Algoritmo de Hopcroft
    while W:
        A = W.pop(0)
        for c in alphabet:
            # X = estados que con c llegan a algún estado en A
            X = set([s for s in states if c in s.transitions and s.transitions[c] in A])
            if not X:
                continue
                
            new_P = []
            for Y in P:
                intersect = Y & X
                diff = Y - X
                
                if intersect and diff:
                    new_P.append(intersect)
                    new_P.append(diff)
                    if Y in W:
                        W.remove(Y)
                        W.append(intersect)
                        W.append(diff)
                    else:
                        if len(intersect) <= len(diff):
                            W.append(intersect)
                        else:
                            W.append(diff)
                else:
                    new_P.append(Y)
            P = new_P

    # 3. Reconstruir el DFA con los nuevos estados
    partition_to_new_state = {}
    for part in P:
        sample = next(iter(part))
        
        # se mezclan los nfa_states de la partición, útil para inspección/debug
        merged_nfa_states = set()
        for s in part:
            merged_nfa_states.update(s.nfa_states)
            
        new_state = DFAState(
            nfa_states=frozenset(merged_nfa_states),
            is_accepting=sample.is_accepting,
            tag=sample.tag
        )
        partition_to_new_state[frozenset(part)] = new_state

    state_to_partition = {}
    for part in P:
        frozen_part = frozenset(part)
        for s in part:
            state_to_partition[s] = frozen_part
            
    # Agregar transiciones
    for part in P:
        sample = next(iter(part))
        frozen_part = frozenset(part)
        new_state = partition_to_new_state[frozen_part]
        
        for c, target in sample.transitions.items():
            target_partition = state_to_partition.get(target)
            if target_partition:
                new_state.add_transition(c, partition_to_new_state[target_partition])

    new_start_state = partition_to_new_state[state_to_partition[dfa.start_state]]
    new_accept_states = set(s for s in partition_to_new_state.values() if s.is_accepting)

    return DFA(new_start_state, new_accept_states)
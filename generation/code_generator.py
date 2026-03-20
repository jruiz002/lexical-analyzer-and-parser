from core.automata import DFA
from core.ast_nodes import YalDocument
import sys

def generate_lexer(doc: YalDocument, dfa: DFA, output_file: str):
    state_to_id = {}
    id_cnt = 0
    for s in dfa.get_states():
        state_to_id[s] = id_cnt
        id_cnt += 1

    transitions = {}
    accepts = {}
    
    for s in dfa.get_states():
        sid = state_to_id[s]
        if s.is_accepting:
            rule_idx, action = s.tag
            accepts[sid] = rule_idx
            
        if s.transitions:
            transitions[sid] = {}
            for c, target in s.transitions.items():
                transitions[sid][c] = state_to_id[target]

    code = []
    
    if doc.header:
        code.append(doc.header.strip())
        code.append("")
        
    code.append(f"START_STATE = {state_to_id[dfa.start_state]}")
    code.append("TRANSITIONS = {")
    for sid, trans in transitions.items():
        code.append(f"    {sid}: {{")
        for c, tid in trans.items():
            code.append(f"        {repr(c)}: {tid},")
        code.append("    },")
    code.append("}")
    code.append("")
    code.append("ACCEPTS = {")
    for sid, rule_idx in accepts.items():
        code.append(f"    {sid}: {rule_idx},")
    code.append("}")
    code.append("")
    
    code.append(f"""
class Lexer:
    def __init__(self, text=None, file_path=None):
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.text = f.read()
        elif text is not None:
            self.text = text
        else:
            raise ValueError("Must provide either 'text' or 'file_path'")
            
        self.pos = 0

    def {doc.entrypoint_name}(self):
        while self.pos < len(self.text) + 1:
            state = START_STATE
            last_accept_idx = -1
            last_accept_pos = -1
            current_pos = self.pos
            
            while current_pos <= len(self.text):
                char = self.text[current_pos] if current_pos < len(self.text) else chr(256)
                
                trans = TRANSITIONS.get(state, {{}})
                next_state = trans.get(char)
                
                if next_state is not None:
                    state = next_state
                    current_pos += 1
                    if state in ACCEPTS:
                        last_accept_idx = ACCEPTS[state]
                        last_accept_pos = current_pos
                else:
                    break
                    
            if last_accept_idx != -1:
                lxm = self.text[self.pos:last_accept_pos]
                if last_accept_pos > len(self.text):
                    lxm = self.text[self.pos:] # ignore EOF character from matched string
                    
                self.pos = last_accept_pos
                lexbuf = self.text # Exposed intentionally for generic usages
""")
    
    first = True
    for i, rule in enumerate(doc.rules):
        prefix = "if" if first else "elif"
        first = False
        code.append(f"                {prefix} last_accept_idx == {i}:")
        if rule.action and rule.action.strip():
            lines = rule.action.strip().splitlines()
            for line in lines:
                code.append(f"                    {line.strip()}")
        else:
            code.append("                    pass")

    code.append("""
            else:
                char_err = self.text[self.pos] if self.pos < len(self.text) else "EOF"
                print(f"Error léxico: secuencia irreconocible '{char_err}' en la posición {self.pos}")
                self.pos += 1
                continue

            if self.pos >= len(self.text) and last_accept_pos > len(self.text):
                break
""")

    if doc.trailer:
        code.append("")
        code.append(doc.trailer.strip())

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(code))

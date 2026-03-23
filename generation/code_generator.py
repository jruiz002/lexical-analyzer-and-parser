from core.automata import DFA
from core.ast_nodes import YalDocument
import re as _re
import sys

def _preprocess_action(action: str) -> str:
    action = _re.sub(r'\breturn\s+lexbuf\b', 'continue', action)
    action = _re.sub(r'\braise\s*\(', 'raise Exception(', action)
    return action

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
    
    # Include Header if present
    if doc.header:
        clean_header = _re.sub(r'\(\*.*?\*\)', '', doc.header, flags=_re.DOTALL).strip()
        if clean_header:
            code.append(clean_header)
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

    # Token constructor helpers
    code.append("# --- Token constructor helpers ---")
    code.append("class _Tok:")
    code.append("    def __init__(self, name): self._name = name")
    code.append("    def __call__(self, lexeme): return (self._name, lexeme)")
    code.append("    def __repr__(self): return self._name")
    code.append("    def __eq__(self, other):")
    code.append("        if isinstance(other, _Tok): return self._name == other._name")
    code.append("        return self._name == other")
    code.append("    def __hash__(self): return hash(self._name)")
    code.append("")

    # Collect all token names used in action blocks
    token_names = set()
    for rule in doc.rules:
        if rule.action:
            for m in _re.finditer(r'\breturn\s+([A-Z_][A-Z0-9_]*)\s*\(', rule.action):
                token_names.add(m.group(1))
            for m in _re.finditer(r'\breturn\s+([A-Z_][A-Z0-9_]*)(?!\s*[\(\w])', rule.action):
                name = m.group(1)
                if name not in ('None', 'True', 'False'):
                    token_names.add(name)

    if token_names:
        code.append("# Auto-generated token constructors from .yal action blocks")
        for name in sorted(token_names):
            code.append(f"{name} = _Tok({repr(name)})")
        code.append("")

    # Lexer engine — now with self.line tracking
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
        self.line = 1

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
                    lxm = self.text[self.pos:]
                self.line += lxm.count('\\n')
                self.pos = last_accept_pos
                lexbuf = self.text  # Exposed intentionally for generic usages
""")

    # Embed rule actions
    first = True
    for i, rule in enumerate(doc.rules):
        prefix = "if" if first else "elif"
        first = False
        code.append(f"                {prefix} last_accept_idx == {i}:")
        if rule.action and rule.action.strip():
            processed = _preprocess_action(rule.action.strip())
            for line in processed.splitlines():
                code.append(f"                    {line.strip()}")
        else:
            code.append("                    pass")

    code.append("""
            else:
                char_err = self.text[self.pos] if self.pos < len(self.text) else "EOF"
                if char_err == '\\n':
                    self.line += 1
                print(f"Error léxico: secuencia irreconocible {repr(char_err)} en la línea {self.line}, posición {self.pos}")
                self.pos += 1
                continue

            if self.pos >= len(self.text) and last_accept_pos > len(self.text):
                break
""")

    if doc.trailer:
        code.append("")
        code.append(doc.trailer.strip())

    # __main__ block
    code.append("")
    code.append("")
    code.append("if __name__ == \"__main__\":")
    code.append("    import sys")
    code.append("    if len(sys.argv) > 1:")
    code.append("        lexer = Lexer(file_path=sys.argv[1])")
    code.append("        print(f\"Tokenizing file: {sys.argv[1]}\")")
    code.append("    else:")
    code.append("        src = input(\"Enter input to tokenize: \")")
    code.append("        lexer = Lexer(text=src)")
    code.append("    print(\"Tokens:\")")
    code.append("    try:")
    code.append("        while True:")
    code.append(f"            tok = lexer.{doc.entrypoint_name}()")
    code.append("            if tok is None:")
    code.append("                continue")
    code.append("            print(\"  \" + str(tok))")
    code.append("            if tok == \"EOF\" or lexer.pos >= len(lexer.text):")
    code.append("                break")
    code.append("    except Exception as e:")
    code.append("        print(f\"  [End of input: {e}]\")")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(code))
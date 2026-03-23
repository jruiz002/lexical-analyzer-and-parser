import argparse
import sys
import os

from parsing.yal_parser import parse_yal
from dfa.regex_expander import expand_document
from dfa.direct_dfa_builder import DirectDFABuilder
from dfa.dfa_minimizer import minimize_dfa
from generation.code_generator import generate_lexer
from core.ast_nodes import YalDocument

def main():
    parser = argparse.ArgumentParser(description="YALex - Yet Another Lexical Analyzer Generator")
    parser.add_argument("input", help="The input .yal file")
    parser.add_argument("-o", "--output", default=os.path.join("output", "thelexer.py"), help="Output generated python lexer file")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: input file '{args.input}' not found.")
        sys.exit(1)

    try:
        print("\n")
        print("-"*50)
        print(f"FASE 1: Lexer y Parser de YALex")
        print(f"- Módulo: parsing.yal_parser")
        print(f"- Entrada: Archivo plano '{args.input}'")
        doc: YalDocument = parse_yal(args.input)
        print(f"- Encontrado:")
        print(f"     - {len(doc.lets)} lets.")
        print(f"     - {len(doc.rules)} rules in entrypoint '{doc.entrypoint_name}'.")

        print("\nAST Generado")
        doc.print_tree()
        print(f"\n- Salida: AST con Estructura Formal (Header, {len(doc.lets)} definitions, {len(doc.rules)} rules)\n")

        print("-"*50)
        print("FASE 2: Expansor de expresiones regulares")
        print(f"- Módulo: dfa.regex_expander")
        print(f"- Entrada: AST del programa")
        expanded_rules = expand_document(doc)
        doc.rules = expanded_rules
        print(f"- Salida: AST con Expresiones Regulares Expandidas ({len(expanded_rules)} rules)\n")

        print("-"*50)
        print("FASE 3: Construcción Directa de DFA")
        print(f"- Módulo: dfa.direct_dfa_builder")
        print(f"- Entrada: Lista de Regex expandidas")
        builder = DirectDFABuilder()
        dfa = builder.build(expanded_rules)
        print(f"- Salida: DFA Global Determinístico ({len(dfa.get_states())} estados)\n")

        print("-"*50)
        print("FASE 4: Minimización de DFA")
        print(f"- Módulo: dfa.dfa_minimizer")
        print(f"- Entrada: DFA Global Determinístico")
        min_dfa = minimize_dfa(dfa)
        print(f"- Salida: DFA Mínimo ({len(min_dfa.get_states())} estados)\n")

        print("-"*50)
        print(f"FASE 5: Generación de código Python")
        print(f"- Módulo: generation.code_generator")
        print(f"- Entrada: DFA Mínimo, Header, Trailer, Action blocks")
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        generate_lexer(doc, min_dfa, args.output)
        print(f"- Salida: Archivo fuente del analizador léxico '{args.output}'")

        print("\nRESULTADO: Compilación de YALex finalizada exitosamente.")

    except Exception as e:
        print(f"Compilation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

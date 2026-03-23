# YALex - Generador de Analizadores Léxicos

## ¿Qué es este proyecto y cuál es su propósito?

Imagina que estás construyendo tu propio lenguaje de programación (o leyendo un formato de archivo muy complejo). El **primer paso** para que una computadora entienda ese texto creado por humanos es separarlo en "palabras" o "fichas" con significado (Tokens). A esta tarea se le llama **Análisis Léxico**.

Escribir un analizador léxico a mano con "if/else" para cada nuevo formato o lenguaje es tedioso y propenso a muchos errores. **El propósito de este proyecto (YALex) es crear un programa de software que escriba ese analizador léxico por ti.**

Es decir, YALex es una "fábrica de analizadores":

1. Tú le das un archivo `.yal` (una receta) súper resumido donde le dices "los números son así", "las palabras son así", "los símbolos de suma son así".
2. YALex lee esa receta, hace matemática de autómatas avanzada por detrás, y **te escupe un archivo de código fuente en Python puro (`thelexer.py`)** completamente nuevo y funcional para leer ese formato.
3. Ese nuevo archivo `thelexer.py` es tu Analizador Léxico Final. Ya lo puedes poner en otro programa propio, pasarle enormes archivos de texto reales, y te encontrará e identificará tokens a la perfección.

---

## Flujo de Trabajo y Ejecución (El Paradigma de Dos Etapas)

Es fundamental comprender que el compilador YALex **no analiza código fuente final**, sino que opera bajo una arquitectura clásica de generación de código separada temporalmente en dos fases distintas:

### Etapa 1: Tiempo de Fabricación (Generador)

El usuario define las clases léxicas, variables y reglas de precedencia de su Lenguaje mediante la Notación Regular proveída por la extensión YALex (por ejemplo, `test.yal`).

- **Input**: Nuestro compilador (`main.py`) recibe el archivo maestro `test.yal`.
- **Proceso**: El Pipeline orquestador (descrito en _Estructura de Módulos_) procesa la matemática computacional, construye el Árbol AST Inicial y su equivalente Autómata Finito Determinístico Mínimo.
- **Output**: Finaliza su ejecución emitiendo un archivo físico de lenguaje Python (`output/thelexer.py`). Esta es "La Máquina Fabricada".

### Etapa 2: Tiempo de Ejecución (Analizador Final)

Dias, meses o años después de ser fabricado, el lexer subyacente cobra vida en integraciones externas o compiladores superiores.

- **Input**: El usuario importa su nuevo `output/thelexer.py` en sus proyectos locales y le envía _Código Fuente en Texto Plano_ (por ejemplo, un archivo llamado `script.test`, o un documento de facturación gigantesco).
- **Output**: Este nuevo ejecutable nativo barre todo el archivo de texto secuencialmente buscando empates en la Cadena más Larga (Longest-Match) y devuelve los Tokens solicitados a nivel de Sistema u emite errores léxicos al detectar caracteres anómalos que no cuadren con las reglas inyectadas originalmente en la _Etapa 1_.

---

## Verificación de Requisitos (100% Cumplido)

El proyecto fue auditado y actualmente cumple a cabalidad con cada línea de las especificaciones:

- **Entrada (Herramienta Generadora):** Recibe como input de consola un archivo configurado bajo la rúbrica oficial YALex (ej. `test.yal`).
- **Salida 1 (Generador):** A partir del input, YALex imprime gráficamente por consola el **Árbol de Expresiones (AST)** visualizando la especificación de componentes léxicos leída.
- **Salida 2 (Generador):** Crea el analizador solicitado escribiendo un programa fuente nuevo nativo llamado `output/thelexer.py` que hereda las reglas extraídas.
- **Entrada (Analizador Generado):** Al invocar la clase base de `thelexer.py`, su objeto recibe obligatoriamente una ruta a un archivo de **texto plano** local (o un string pre-copiado).
- **Salida (Analizador Generado):** Durante el bucle de procesamiento de texto plano, imprime asíncronamente en pantalla cada **Token** verificado y emparejado, o en su defecto, atrapa flujos vacíos enviando hermosos **mensajes documentados sobre el error léxico**.

---

## Explicación Arquitectónica: Estructura de Módulos

El funcionamiento interno consiste en un patrón de diseño _Pipeline_ (similar a una línea de la cadena de ensamblaje en una fábrica de autos). Entra tu receta `.yal` cruda por un extremo, viaja procesándose a través de 5 Departamentos lógicos secuenciales, y sale un Script funcional de Python por el lado opuesto.

### `main.py` (El Gerente del Sistema)

Punto de Entrada CLI del programa. Evalúa rutas, y si todo está válido empuja la información del flujo de principio a fin coordinando cada departamento.

### Carpeta `parsing/` (El Departamento de Lectura)

Su trabajo es leer lo aburrido de tu archivo original y prepararlo para la máquina. Convierte texto estructurado en el "Árbol".

- **`yal_lexer.py`**: Recorre el archivo `.yal` limpiando código (vota strings vacios y obvia los comentarios `(* *)`). Recoge piezas vitales y avisan "acá hay una regla", "aca hay un identificador".
- **`yal_parser.py`**: Conector Gramatical. Recibe esas piezas de información cortadas y construye lógicamente el **Árbol Abstracto de Sintaxis (AST)**. Organiza de lado izquierdo reglas, verifica que hayas escrito el YALex bajo reglas correctas e intenta no romper el árbol.

### Carpeta `dfa/` (El Departamento de Matemática Compilatoria)

Una computadora jamás podría usar las "Expresiones Regulares" de manera veloz con expresiones como `(A-Z)+` en código puro. Necesitan traducir esas letras a mapas relacionales binarios conocidos como "Máquinas de Estado" o DFA.

- **`regex_expander.py`**: Resuelve la dependencia contextual de tus regex. Agarra variables guardadas tempranamente en tu archivo (ej. `let num = ['0'-'9']`) e inyecta literalmente su expresión base dondequiera que tú utilices `num` después en tu archivo.
- **`direct_dfa_builder.py`**: Realiza cálculos topológicos directos usando las funciones teóricas pre-compilatorias (`firstpost`, `lastpos`, `nullable`, etc) para generar de cero un Autómata Finito Determinista basándose únicamente en la red topológica del Árbol. Acá también está construida la resolución analítica para empatar siempre "La coincidencia más Grande (Longest Match)" e indizar prioridades en empates de reconocimiento de token.
- **`dfa_minimizer.py`**: El Autómata arrojado en el archivo previo matemáticamente no comete fallos pero está crudo, gordo e inflado de estados transitorios inútiles. Acá se corre el popular **Algoritmo de Hopcroft**. Su meta: Recortar y agrupar nodos transicionales equivalentes achicando brutalmente a niveles optimos la memoria matemática que un Analizador requiere para existir... pero obligándolo a nunca fusionar terminales de distinción que maten el proyecto.

### Carpeta `generation/` (El Departamento Escritor y Transpilador)

- **`code_generator.py`**: Su cliente es el algoritmo mínimo procesado en la etapa de dfa. Transforma variables en memorias in-RAM hacia su texto sintáctico exacto de Python real. Carga tus fragmentos embutidos pasados por la opción `{ action }` condicionalmente por debajo del ciclo evaluativo del script pitónico general para correr tu instrucción particular al detectar el reconocimiento de tu sintaxis customizada. Como salida produce un nuevo script empaquetado y listo para ser corrido por Python: `thelexer.py`.

### Carpeta `core/` (Entidades Estructurales)

- Son simples clases orientadas a objetos (`ast_nodes.py` y `automata.py`) que dictaminan los límites de propiedad o funciones con los cuáles los 5 departamentos interactuan entre sí. No aplican comportamiento directo, pero mantienen el tipo y seguridad del ecosistema.

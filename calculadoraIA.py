# calculadora_windows.py
# Calculadora estilo "Calculadora de Windows" (tema claro)
# - Solo usa tkinter (incluido con Python, no requiere instalar nada)
# - Evaluación segura con AST (sin eval)

import ast
import math
import tkinter as tk

# ============================================================
# Motor de evaluación segura (sin eval)
# ============================================================

class ErrorCalculo(Exception):
    pass


OPERADORES = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}


def evaluar(expresion: str) -> float:
    if not expresion or not expresion.strip():
        raise ErrorCalculo("Vacío")

    expresion = expresion.replace("×", "*").replace("÷", "/")

    try:
        arbol = ast.parse(expresion, mode="eval")
    except SyntaxError:
        raise ErrorCalculo("Entrada no válida")

    return _evaluar_nodo(arbol.body)


def _evaluar_nodo(nodo):
    if isinstance(nodo, ast.Constant):
        if isinstance(nodo.value, (int, float)):
            return float(nodo.value)
        raise ErrorCalculo("Valor inválido")

    if isinstance(nodo, ast.BinOp):
        izq = _evaluar_nodo(nodo.left)
        der = _evaluar_nodo(nodo.right)
        tipo_op = type(nodo.op)
        if tipo_op not in OPERADORES:
            raise ErrorCalculo("Operación no permitida")
        if tipo_op is ast.Div and der == 0:
            raise ErrorCalculo("No se puede dividir entre cero")
        resultado = OPERADORES[tipo_op](izq, der)
        if isinstance(resultado, complex) or math.isnan(resultado) or math.isinf(resultado):
            raise ErrorCalculo("Resultado inválido")
        return resultado

    if isinstance(nodo, ast.UnaryOp):
        val = _evaluar_nodo(nodo.operand)
        if isinstance(nodo.op, ast.USub):
            return -val
        if isinstance(nodo.op, ast.UAdd):
            return val
        raise ErrorCalculo("Operación no permitida")

    raise ErrorCalculo("Entrada no válida")


def formatear(numero: float) -> str:
    if math.isnan(numero) or math.isinf(numero):
        return "Error"
    if abs(numero - round(numero)) < 1e-10:
        return str(int(round(numero)))
    texto = f"{numero:.10f}".rstrip("0").rstrip(".")
    if len(texto) > 16:
        texto = f"{numero:.6e}"
    return texto


# ============================================================
# Paleta "Calculadora de Windows" (tema claro)
# ============================================================

COLOR_FONDO = "#F3F3F3"
COLOR_DISPLAY_BG = "#FFFFFF"
COLOR_BORDE_DISPLAY = "#1B1B1B"
COLOR_TEXTO = "#1B1B1B"
COLOR_TEXTO_MEMORIA = "#B0B0B0"

COLOR_BTN_NUM = "#FFFFFF"
COLOR_BTN_NUM_HOVER = "#E9E9E9"
COLOR_BTN_NUM_BORDE = "#E5E5E5"

COLOR_BTN_FUNC = "#F3F3F3"
COLOR_BTN_FUNC_HOVER = "#E4E4E4"

COLOR_BTN_OP = "#F3F3F3"
COLOR_BTN_OP_HOVER = "#E4E4E4"

COLOR_ACENTO = "#0067C0"
COLOR_ACENTO_HOVER = "#1975C4"
COLOR_TEXTO_ACENTO = "#FFFFFF"


class Boton(tk.Button):
    """Botón plano estilo Windows con efecto hover."""

    def __init__(self, master, texto, comando, color_normal, color_hover,
                 color_texto=COLOR_TEXTO, tam_fuente=16, borde=False, **kwargs):
        cfg = dict(
            text=texto,
            command=comando,
            bg=color_normal,
            fg=color_texto,
            activebackground=color_hover,
            activeforeground=color_texto,
            font=("Segoe UI", tam_fuente),
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        if borde:
            cfg.update(highlightthickness=1, highlightbackground=COLOR_BTN_NUM_BORDE,
                       highlightcolor=COLOR_BTN_NUM_BORDE)
        cfg.update(kwargs)
        super().__init__(master, **cfg)
        self.color_normal = color_normal
        self.color_hover = color_hover
        self.bind("<Enter>", lambda e: self.configure(bg=self.color_hover))
        self.bind("<Leave>", lambda e: self.configure(bg=self.color_normal))


class CalculadoraWindows:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calculadora")
        self.root.geometry("340x520")
        self.root.minsize(300, 480)
        self.root.configure(bg=COLOR_FONDO)

        self.entrada = tk.StringVar(value="0")
        self.memoria = None
        self.valor_previo = None       # primer operando guardado
        self.operador_pendiente = None  # '+', '-', '*', '/'
        self.reemplazar_en_siguiente_digito = False

        self._construir_titulo()
        self._construir_display()
        self._construir_memoria()
        self._construir_teclado()

        self.root.bind("<Key>", self._tecla_presionada)
        self.root.bind("<Return>", lambda e: self._igual())
        self.root.bind("<BackSpace>", lambda e: self._borrar())
        self.root.bind("<Escape>", lambda e: self._limpiar_todo())

    # -----------------------------
    # Construcción de la interfaz
    # -----------------------------
    def _construir_titulo(self):
        barra = tk.Frame(self.root, bg=COLOR_FONDO, height=36)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        tk.Label(barra, text="≡  Estándar", bg=COLOR_FONDO, fg=COLOR_TEXTO,
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", padx=10)

    def _construir_display(self):
        marco = tk.Frame(self.root, bg=COLOR_DISPLAY_BG, highlightthickness=2,
                          highlightbackground=COLOR_BORDE_DISPLAY, highlightcolor=COLOR_BORDE_DISPLAY)
        marco.pack(fill="x", padx=10, pady=(6, 10))

        self.lbl_entrada = tk.Label(
            marco, textvariable=self.entrada, bg=COLOR_DISPLAY_BG, fg=COLOR_TEXTO,
            font=("Segoe UI", 40), anchor="e", padx=14, pady=18
        )
        self.lbl_entrada.pack(fill="x")

    def _construir_memoria(self):
        marco = tk.Frame(self.root, bg=COLOR_FONDO)
        marco.pack(fill="x", padx=10, pady=(0, 6))
        for i in range(6):
            marco.grid_columnconfigure(i, weight=1)

        botones_mem = [
            ("MC", self._mem_limpiar),
            ("MR", self._mem_recuperar),
            ("M+", self._mem_sumar),
            ("M-", self._mem_restar),
            ("MS", self._mem_guardar),
            ("M∨", self._mem_recuperar),
        ]
        self.botones_memoria = []
        for i, (texto, accion) in enumerate(botones_mem):
            b = Boton(marco, texto, accion, COLOR_FONDO, "#E4E4E4",
                      color_texto=COLOR_TEXTO_MEMORIA, tam_fuente=10)
            b.grid(row=0, column=i, sticky="nsew", padx=2)
            self.botones_memoria.append(b)
        self._actualizar_estado_memoria()

    def _construir_teclado(self):
        marco = tk.Frame(self.root, bg=COLOR_FONDO)
        marco.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        for i in range(6):
            marco.grid_rowconfigure(i, weight=1)
        for i in range(4):
            marco.grid_columnconfigure(i, weight=1)

        # Fila 0: % CE C ⌫
        Boton(marco, "%", self._porcentaje, COLOR_BTN_FUNC, COLOR_BTN_FUNC_HOVER,
              tam_fuente=13).grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        Boton(marco, "CE", self._limpiar_entrada, COLOR_BTN_FUNC, COLOR_BTN_FUNC_HOVER,
              tam_fuente=13).grid(row=0, column=1, sticky="nsew", padx=3, pady=3)
        Boton(marco, "C", self._limpiar_todo, COLOR_BTN_FUNC, COLOR_BTN_FUNC_HOVER,
              tam_fuente=13).grid(row=0, column=2, sticky="nsew", padx=3, pady=3)
        Boton(marco, "⌫", self._borrar, COLOR_BTN_FUNC, COLOR_BTN_FUNC_HOVER,
              tam_fuente=13).grid(row=0, column=3, sticky="nsew", padx=3, pady=3)

        # Fila 1: 1/x  x²  ²√x  ÷
        Boton(marco, "1/x", self._reciproco, COLOR_BTN_FUNC, COLOR_BTN_FUNC_HOVER,
              tam_fuente=13).grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        Boton(marco, "x²", self._cuadrado, COLOR_BTN_FUNC, COLOR_BTN_FUNC_HOVER,
              tam_fuente=13).grid(row=1, column=1, sticky="nsew", padx=3, pady=3)
        Boton(marco, "²√x", self._raiz, COLOR_BTN_FUNC, COLOR_BTN_FUNC_HOVER,
              tam_fuente=13).grid(row=1, column=2, sticky="nsew", padx=3, pady=3)
        Boton(marco, "÷", lambda: self._operador("/"), COLOR_BTN_OP, COLOR_BTN_OP_HOVER,
              tam_fuente=18).grid(row=1, column=3, sticky="nsew", padx=3, pady=3)

        # Filas de números 7-8-9 / 4-5-6 / 1-2-3, con operadores a la derecha
        filas_numeros = [
            (["7", "8", "9"], "×", "*"),
            (["4", "5", "6"], "-", "-"),
            (["1", "2", "3"], "+", "+"),
        ]
        for r, (nums, simbolo_op, valor_op) in enumerate(filas_numeros, start=2):
            for c, n in enumerate(nums):
                Boton(marco, n, lambda d=n: self._digito(d), COLOR_BTN_NUM, COLOR_BTN_NUM_HOVER,
                      tam_fuente=18, borde=True).grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
            Boton(marco, simbolo_op, lambda v=valor_op: self._operador(v), COLOR_BTN_OP, COLOR_BTN_OP_HOVER,
                  tam_fuente=18).grid(row=r, column=3, sticky="nsew", padx=3, pady=3)

        # Fila final: +/-  0  .  =
        Boton(marco, "+/-", self._cambiar_signo, COLOR_BTN_NUM, COLOR_BTN_NUM_HOVER,
              tam_fuente=15, borde=True).grid(row=5, column=0, sticky="nsew", padx=3, pady=3)
        Boton(marco, "0", lambda: self._digito("0"), COLOR_BTN_NUM, COLOR_BTN_NUM_HOVER,
              tam_fuente=18, borde=True).grid(row=5, column=1, sticky="nsew", padx=3, pady=3)
        Boton(marco, ".", lambda: self._digito("."), COLOR_BTN_NUM, COLOR_BTN_NUM_HOVER,
              tam_fuente=18, borde=True).grid(row=5, column=2, sticky="nsew", padx=3, pady=3)
        Boton(marco, "=", self._igual, COLOR_ACENTO, COLOR_ACENTO_HOVER,
              color_texto=COLOR_TEXTO_ACENTO, tam_fuente=18).grid(row=5, column=3, sticky="nsew", padx=3, pady=3)

    # -----------------------------
    # Entrada numérica
    # -----------------------------
    def _digito(self, d):
        actual = self.entrada.get()
        if self.reemplazar_en_siguiente_digito or actual == "0":
            actual = ""
            self.reemplazar_en_siguiente_digito = False
        if d == "." and "." in actual:
            return
        nuevo = actual + d
        self.entrada.set(nuevo if nuevo else "0")
        self._ajustar_tamano_fuente()

    def _ajustar_tamano_fuente(self):
        largo = len(self.entrada.get())
        tam = 40
        if largo > 9:
            tam = 30
        if largo > 13:
            tam = 22
        if largo > 18:
            tam = 16
        self.lbl_entrada.configure(font=("Segoe UI", tam))

    def _borrar(self):
        actual = self.entrada.get()
        if self.reemplazar_en_siguiente_digito or len(actual) <= 1:
            self.entrada.set("0")
        else:
            self.entrada.set(actual[:-1])
        self._ajustar_tamano_fuente()

    def _limpiar_entrada(self):
        self.entrada.set("0")
        self.reemplazar_en_siguiente_digito = False
        self._ajustar_tamano_fuente()

    def _limpiar_todo(self):
        self.entrada.set("0")
        self.valor_previo = None
        self.operador_pendiente = None
        self.reemplazar_en_siguiente_digito = False
        self.lbl_entrada.configure(fg=COLOR_TEXTO)
        self._ajustar_tamano_fuente()

    def _cambiar_signo(self):
        actual = self.entrada.get()
        if actual in ("0", ""):
            return
        self.entrada.set(actual[1:] if actual.startswith("-") else "-" + actual)

    # -----------------------------
    # Operaciones encadenadas (estilo calculadora real: 5 + 3 + 2 =)
    # -----------------------------
    def _operador(self, simbolo):
        try:
            actual = float(self.entrada.get())
        except ValueError:
            self._mostrar_error("Entrada no válida")
            return

        if self.operador_pendiente and not self.reemplazar_en_siguiente_digito:
            # Encadena: resuelve lo pendiente antes de aplicar el nuevo operador
            self._resolver_pendiente(actual)
        else:
            self.valor_previo = actual

        self.operador_pendiente = simbolo
        self.reemplazar_en_siguiente_digito = True

    def _resolver_pendiente(self, segundo_operando):
        try:
            expr = f"{self.valor_previo}{self.operador_pendiente}{segundo_operando}"
            resultado = evaluar(expr)
            self.valor_previo = resultado
            self.entrada.set(formatear(resultado))
            self._ajustar_tamano_fuente()
        except ErrorCalculo as e:
            self._mostrar_error(str(e))

    def _igual(self):
        if self.operador_pendiente is None:
            return
        try:
            actual = float(self.entrada.get())
        except ValueError:
            self._mostrar_error("Entrada no válida")
            return

        self._resolver_pendiente(actual)
        self.operador_pendiente = None
        self.reemplazar_en_siguiente_digito = True

        # Destello de confirmación
        self.lbl_entrada.configure(fg=COLOR_ACENTO)
        self.root.after(180, lambda: self.lbl_entrada.configure(fg=COLOR_TEXTO))

    # -----------------------------
    # Funciones de un solo operando
    # -----------------------------
    def _aplicar_funcion(self, func, nombre_error="Entrada no válida"):
        try:
            actual = float(self.entrada.get())
            resultado = func(actual)
            if math.isnan(resultado) or math.isinf(resultado):
                raise ValueError
            self.entrada.set(formatear(resultado))
            self.reemplazar_en_siguiente_digito = True
            self._ajustar_tamano_fuente()
        except (ValueError, ZeroDivisionError):
            self._mostrar_error(nombre_error)

    def _reciproco(self):
        self._aplicar_funcion(lambda x: 1 / x, "No se puede dividir entre cero")

    def _cuadrado(self):
        self._aplicar_funcion(lambda x: x * x)

    def _raiz(self):
        self._aplicar_funcion(lambda x: math.sqrt(x), "Entrada inválida")

    def _porcentaje(self):
        try:
            actual = float(self.entrada.get())
            base = self.valor_previo if self.valor_previo is not None else actual
            resultado = base * actual / 100
            self.entrada.set(formatear(resultado))
            self.reemplazar_en_siguiente_digito = True
            self._ajustar_tamano_fuente()
        except ValueError:
            self._mostrar_error("Entrada no válida")

    def _mostrar_error(self, mensaje):
        self.entrada.set(mensaje)
        self.lbl_entrada.configure(fg="#C42B1C", font=("Segoe UI", 22))
        self.valor_previo = None
        self.operador_pendiente = None
        self.root.after(1300, self._limpiar_todo)

    # -----------------------------
    # Memoria
    # -----------------------------
    def _actualizar_estado_memoria(self):
        activo = self.memoria is not None
        color = COLOR_TEXTO if activo else COLOR_TEXTO_MEMORIA
        for b in self.botones_memoria[:2]:  # MC, MR
            b.configure(fg=color)
        self.botones_memoria[5].configure(fg=color)  # M∨

    def _mem_limpiar(self):
        self.memoria = None
        self._actualizar_estado_memoria()

    def _mem_recuperar(self):
        if self.memoria is None:
            return
        self.entrada.set(formatear(self.memoria))
        self.reemplazar_en_siguiente_digito = True
        self._ajustar_tamano_fuente()

    def _mem_sumar(self):
        try:
            actual = float(self.entrada.get())
            self.memoria = (self.memoria or 0) + actual
            self.reemplazar_en_siguiente_digito = True
            self._actualizar_estado_memoria()
        except ValueError:
            pass

    def _mem_restar(self):
        try:
            actual = float(self.entrada.get())
            self.memoria = (self.memoria or 0) - actual
            self.reemplazar_en_siguiente_digito = True
            self._actualizar_estado_memoria()
        except ValueError:
            pass

    def _mem_guardar(self):
        try:
            self.memoria = float(self.entrada.get())
            self.reemplazar_en_siguiente_digito = True
            self._actualizar_estado_memoria()
        except ValueError:
            pass

    # -----------------------------
    # Atajos de teclado
    # -----------------------------
    def _tecla_presionada(self, evento):
        car = evento.char
        if car in "0123456789":
            self._digito(car)
        elif car == ".":
            self._digito(".")
        elif car in "+-":
            self._operador(car)
        elif car == "*":
            self._operador("*")
        elif car == "/":
            self._operador("/")
        elif car == "%":
            self._porcentaje()

    def ejecutar(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = CalculadoraWindows()
        app.ejecutar()
    except Exception as error:
        import traceback
        import tkinter.messagebox as mb

        traceback.print_exc()
        root_error = tk.Tk()
        root_error.withdraw()
        mb.showerror("Error al iniciar la calculadora", f"{type(error).__name__}: {error}")
        raise

"""Interfaz gráfica para visualizar la altura del líquido en un tanque cilíndrico horizontal."""

import math
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from matplotlib.ticker import MaxNLocator

from altura import calcular_altura_con_iteraciones, funciones_newton, volumen_maximo

""" TanqueModel, que funciona como el "cerebro" o la memoria central de tu interfaz 
gráfica.
En desarrollo de software, esto se conoce como el patrón de diseño MVC (Modelo-Vista-Controlador). 
TanqueModel es el "Modelo": almacenar los datos físicos del tanque y garantizar que siempre tengan 
sentido matemático, para que las distintas pestañas ("Vistas") consulten exactamente la misma 
información y no se desincronicen. """

class TanqueModel:
    """Estado compartido entre pestañas."""

    def __init__(self):
        self.diametro = 5.0
        self.longitud = 10.0
        self.volumen = 0.0

    @property
    def radio(self):
        return self.diametro / 2.0

    @property
    def volumen_max(self):
        return volumen_maximo(self.diametro, self.longitud)

    def ajustar_volumen(self):
        self.volumen = max(0.0, min(self.volumen, self.volumen_max))

    def actualizar_dimensiones(self, diametro, longitud, mantener_porcentaje=True):
        pct = self.volumen / self.volumen_max if self.volumen_max > 0 else 0.0
        self.diametro = diametro
        self.longitud = longitud
        if mantener_porcentaje:
            self.volumen = pct * self.volumen_max
        self.ajustar_volumen()

    def altura_e_iteraciones(self):
        return calcular_altura_con_iteraciones(self.volumen, self.diametro, self.longitud)


def poligono_liquido_2d(R, h):
    """Polígono del segmento circular lleno (vista frontal: ancho x altura y)."""
    if h <= 0:
        return np.empty((0, 2))
    cx, cy = R, R
    if h >= 2 * R:
        theta = np.linspace(0, 2 * math.pi, 120)
        return np.column_stack((cx + R * np.cos(theta), cy + R * np.sin(theta)))

    dy = h - cy
    dx = math.sqrt(max(R * R - dy * dy, 0.0))
    x_izq, x_der = cx - dx, cx + dx
    ang_der = math.atan2(dy, dx)
    ang_izq = math.atan2(dy, -dx)

    # Arco que pasa por el fondo del cilindro (-pi/2) = region y <= h (liquido)
    if h <= R:
        if ang_der > ang_izq:
            theta_arco = np.linspace(ang_der, ang_izq, 80)
        else:
            theta_arco = np.linspace(ang_der, ang_izq - 2 * math.pi, 80)
    else:
        theta_arco = np.linspace(ang_izq, ang_der + 2 * math.pi, 80)

    x_arco = cx + R * np.cos(theta_arco)
    y_arco = cy + R * np.sin(theta_arco)

    return np.column_stack(
        (
            np.concatenate(([x_der], x_arco, [x_izq])),
            np.concatenate(([h], y_arco, [h])),
        )
    )


def malla_cilindro_3d(R, L, res_theta=48, res_x=24):
    """Cilindro horizontal: eje X = longitud, seccion circular en el plano Y-Z."""
    theta = np.linspace(0, 2 * math.pi, res_theta)
    x = np.linspace(0, L, res_x)
    x_grid, theta_grid = np.meshgrid(x, theta)
    y = R + R * np.cos(theta_grid)
    z = R + R * np.sin(theta_grid)
    return x_grid, y, z


def caras_liquido_3d(R, L, h):
    """Caras 3D del liquido extruido a lo largo del eje X."""
    poly = poligono_liquido_2d(R, h)
    if poly.shape[0] < 3:
        return []

    n = len(poly)
    faces = [
        [(0.0, p[0], p[1]) for p in poly],
        [(L, p[0], p[1]) for p in poly],
    ]
    for i in range(n):
        j = (i + 1) % n
        p0, p1 = poly[i], poly[j]
        faces.append(
            [
                (0.0, p0[0], p0[1]),
                (0.0, p1[0], p1[1]),
                (L, p1[0], p1[1]),
                (L, p0[0], p0[1]),
            ]
        )
    return faces


def _set_aspecto_3d(ax, lx, ly, lz):
    """Escala uniforme para que el cilindro no se deforme y limpia los ejes."""
    ax.set_xlim(0, lx)
    ax.set_ylim(0, ly)
    ax.set_zlim(0, lz)

    # 1. Limitar a un máximo de 5 divisiones (números) por eje
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.zaxis.set_major_locator(MaxNLocator(nbins=5))
    
    # 2. Reducir el tamaño de la fuente y empujar los números hacia atrás
    ax.tick_params(axis='x', labelsize=8, pad=-2)
    ax.tick_params(axis='y', labelsize=8, pad=-2)
    ax.tick_params(axis='z', labelsize=8, pad=2)
    
    try:
        ax.set_box_aspect((lx, ly, lz))
    except AttributeError:
        pass
    # Incrementa el zoom para aprovechar los costados (por defecto es 1.0)
    try:
        ax.set_zoom(4)
    except AttributeError:
        ax.dist = 7  # Para versiones anteriores de Matplotlib

class PestañaInicio(ttk.Frame):
    def __init__(self, master, model, on_change):
        super().__init__(master)
        self.model = model
        self.on_change = on_change

        ctrl = ttk.Frame(self)
        ctrl.pack(fill=tk.X, padx=12, pady=8)

        ttk.Label(ctrl, text="Volumen del líquido (m³):").pack(side=tk.LEFT)
        self.var_volumen = tk.DoubleVar(value=self.model.volumen)
        self.lbl_volumen = ttk.Label(ctrl, text="0.000", width=10)
        self.lbl_volumen.pack(side=tk.RIGHT)

        self.slider = ttk.Scale(
            self,
            from_=0.0,
            to=self.model.volumen_max,
            orient=tk.HORIZONTAL,
            variable=self.var_volumen,
            command=self._on_slider,
        )
        self.slider.pack(fill=tk.X, padx=12)

        info = ttk.Frame(self)
        info.pack(fill=tk.X, padx=12, pady=4)
        self.lbl_altura = ttk.Label(info, text="Altura: 0.000 m")
        self.lbl_altura.pack(side=tk.LEFT, padx=(0, 20))
        self.lbl_porcentaje = ttk.Label(info, text="Llenado: 0.0 %")
        self.lbl_porcentaje.pack(side=tk.LEFT, padx=(0, 20))
        self.lbl_dim = ttk.Label(info, text="")
        self.lbl_dim.pack(side=tk.LEFT)

        fig, self.ax = plt.subplots(figsize=(6, 5))
        fig.patch.set_facecolor("#f5f5f5")
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.actualizar()

    def _on_slider(self, _=None):
        self.model.volumen = float(self.var_volumen.get())
        self.on_change(origen="inicio")

    def sincronizar_controles(self):
        vmax = self.model.volumen_max
        self.slider.configure(to=max(vmax, 0.001))
        self.var_volumen.set(self.model.volumen)

    def actualizar(self):
        self.sincronizar_controles()
        R = self.model.radio
        altura, _ = self.model.altura_e_iteraciones()
        pct = (self.model.volumen / self.model.volumen_max * 100) if self.model.volumen_max else 0

        self.lbl_volumen.config(text=f"{self.model.volumen:.3f}")
        self.lbl_altura.config(text=f"Altura: {altura:.4f} m")
        self.lbl_porcentaje.config(text=f"Llenado: {pct:.1f} %")
        self.lbl_dim.config(
            text=f"D = {self.model.diametro:.2f} m  |  L = {self.model.longitud:.2f} m  |  Vmax = {self.model.volumen_max:.2f} m³"
        )

        self.ax.clear()
        self.ax.set_aspect("equal")
        self.ax.set_xlim(-0.3, 2 * R + 0.3)
        self.ax.set_ylim(-0.3, 2 * R + 0.3)
        self.ax.set_title("Vista frontal del tanque")
        self.ax.set_xlabel("Ancho (m)")
        self.ax.set_ylabel("Altura (m)")

        theta = np.linspace(0, 2 * math.pi, 200)
        xc = R + R * np.cos(theta)
        yc = R + R * np.sin(theta)
        self.ax.add_patch(Polygon(np.column_stack((xc, yc)), closed=True, facecolor="#ffffff", edgecolor="black", lw=2))

        poly = poligono_liquido_2d(R, altura)
        if poly.shape[0] >= 3:
            self.ax.add_patch(Polygon(poly, closed=True, facecolor="#4da6ff", alpha=0.85, edgecolor="#1a6fb5", lw=0.8))

        if 0 < altura < 2 * R:
            self.ax.axhline(altura, color="#1a6fb5", ls="--", lw=1.2)
            self.ax.text(2 * R + 0.5, altura, f"h = {altura:.3f} m", va="center", fontsize=9)

        self.ax.axhline(0, color="#888", lw=0.8)
        self.canvas.draw()


class PestañaParametros(ttk.Frame):
    def __init__(self, master, model, on_change):
        super().__init__(master)
        self.model = model
        self.on_change = on_change

        ctrl = ttk.LabelFrame(self, text="Dimensiones del cilindro")
        ctrl.pack(fill=tk.X, padx=12, pady=10)

        fila_d = ttk.Frame(ctrl)
        fila_d.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(fila_d, text="Diámetro D (m):").pack(side=tk.LEFT)
        self.var_diametro = tk.DoubleVar(value=self.model.diametro)
        ttk.Spinbox(
            fila_d,
            from_=0.5,
            to=20.0,
            increment=0.1,
            textvariable=self.var_diametro,
            width=8,
            command=self._aplicar,
        ).pack(side=tk.RIGHT)
        self.slider_d = ttk.Scale(
            ctrl, from_=0.5, to=20.0, orient=tk.HORIZONTAL, variable=self.var_diametro, command=self._aplicar
        )
        self.slider_d.pack(fill=tk.X, padx=8, pady=(0, 6))

        fila_l = ttk.Frame(ctrl)
        fila_l.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(fila_l, text="Longitud L (m):").pack(side=tk.LEFT)
        self.var_longitud = tk.DoubleVar(value=self.model.longitud)
        ttk.Spinbox(
            fila_l,
            from_=1.0,
            to=50.0,
            increment=0.5,
            textvariable=self.var_longitud,
            width=8,
            command=self._aplicar,
        ).pack(side=tk.RIGHT)
        self.slider_l = ttk.Scale(
            ctrl, from_=1.0, to=50.0, orient=tk.HORIZONTAL, variable=self.var_longitud, command=self._aplicar
        )
        self.slider_l.pack(fill=tk.X, padx=8, pady=(0, 6))

        self.var_diametro.trace_add("write", self._on_var_change)
        self.var_longitud.trace_add("write", self._on_var_change)
        self._syncing = False

        self.lbl_resumen = ttk.Label(ctrl, text="")
        self.lbl_resumen.pack(padx=8, pady=(0, 8))

        # 1. Definir la figura con una relación muy panorámica (12 de ancho por 4 de alto)
        fig = plt.figure(figsize=(10, 3.5))
        fig.patch.set_facecolor("#f5f5f5")

        # [left, bottom, width, height] en proporción (0 a 1)
        # Ocupa desde el borde izquierdo (0) al derecho (1)
        self.ax3d = fig.add_axes([-0.1, -0.1, 1.2, 1.2], projection="3d")
        self.ax3d.set_facecolor("#f5f5f5")

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.actualizar()

    def _on_var_change(self, *_):
        self.after_idle(self._aplicar)

    def _aplicar(self, _=None):
        if self._syncing:
            return
        try:
            d = float(self.var_diametro.get())
            l = float(self.var_longitud.get())
        except tk.TclError:
            return
        d = max(0.5, min(d, 20.0))
        l = max(1.0, min(l, 50.0))
        if abs(d - self.model.diametro) < 1e-9 and abs(l - self.model.longitud) < 1e-9:
            return
        self.model.actualizar_dimensiones(d, l, mantener_porcentaje=True)
        self.on_change(origen="parametros")

    def sincronizar_controles(self):
        self._syncing = True
        self.var_diametro.set(round(self.model.diametro, 2))
        self.var_longitud.set(round(self.model.longitud, 2))
        self._syncing = False

    def actualizar(self):
        self.sincronizar_controles()
        R = self.model.radio
        L = self.model.longitud
        altura, _ = self.model.altura_e_iteraciones()

        self.lbl_resumen.config(
            text=(
                f"Radio R = {R:.2f} m  |  Longitud L = {L:.2f} m  |  "
                f"Volumen máximo = {self.model.volumen_max:.2f} m³"
            )
        )

        self.ax3d.clear()
        x, y, z = malla_cilindro_3d(R, L)
        self.ax3d.plot_surface(x, y, z, color="#d0d0d0", alpha=0.22, linewidth=0, shade=True, rstride=2, cstride=2)

        faces = caras_liquido_3d(R, L, altura)
        if faces:
            poly3d = Poly3DCollection(
                faces, facecolors="#4da6ff", edgecolors="#1a6fb5", alpha=0.72, linewidths=0.35
            )
            self.ax3d.add_collection3d(poly3d)

        self.ax3d.set_xlabel("Longitud X (m)")
        self.ax3d.set_ylabel("Ancho Y (m)")
        self.ax3d.set_zlabel("Altura Z (m)")
        self.ax3d.set_title("Tanque cilíndrico horizontal (eje X = longitud)")
        _set_aspecto_3d(self.ax3d, L, 2 * R, 2 * R)
        # 1. Configurar el ángulo de visión isométrico (Elevación y Azimut)
        # elev = 30-35° da la inclinación superior adecuada.
        # azim = -60° o -45° orienta los ejes X e Y de forma equilibrada.
        self.ax3d.view_init(elev=10, azim=-40)
        self.canvas.draw()


class PestañaCalculos(ttk.Frame):
    def __init__(self, master, model, on_change):
        super().__init__(master)
        self.model = model
        self.on_change = on_change

        self.paso_actual = 0
        self.iteraciones = []
        self.frames = []
        self.anim_id = None
        self.reproduciendo = False

        ctrl = ttk.LabelFrame(self, text="Animación de convergencia (Newton-Raphson)")
        ctrl.pack(fill=tk.X, padx=12, pady=8)

        botones = ttk.Frame(ctrl)
        botones.pack(fill=tk.X, padx=8, pady=6)
        self.btn_play = ttk.Button(botones, text="▶ Play", command=self.toggle_play)
        self.btn_play.pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(botones, text="⟲ Reiniciar", command=self.reiniciar).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(botones, text="⏭ Paso", command=self.siguiente_paso).pack(side=tk.LEFT)

        ttk.Label(botones, text="Intervalo (ms):").pack(side=tk.LEFT, padx=(16, 4))
        self.var_intervalo = tk.IntVar(value=700)
        ttk.Spinbox(botones, from_=100, to=3000, increment=100, textvariable=self.var_intervalo, width=6).pack(
            side=tk.LEFT
        )

        self.lbl_estado = ttk.Label(ctrl, text="")
        self.lbl_estado.pack(padx=8, pady=(0, 8))

        fig, (self.ax_func, self.ax_alt) = plt.subplots(1, 2, figsize=(10, 4.5))
        fig.patch.set_facecolor("#f5f5f5")
        fig.tight_layout(pad=2.0)
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.actualizar()

    def toggle_play(self):
        if self.reproduciendo:
            self.pausar()
        else:
            self.reproducir()

    def reproducir(self):
        if not self.frames:
            return
        if self.paso_actual >= len(self.frames):
            self.paso_actual = 0
        self.reproduciendo = True
        self.btn_play.config(text="⏸ Pausa")
        self._animar()

    def pausar(self):
        self.reproduciendo = False
        self.btn_play.config(text="▶ Play")
        if self.anim_id is not None:
            self.after_cancel(self.anim_id)
            self.anim_id = None

    def reiniciar(self):
        self.pausar()
        self.paso_actual = 0
        self._dibujar_frame()

    def siguiente_paso(self):
        if not self.frames:
            return
        if self.paso_actual < len(self.frames):
            self.paso_actual += 1
            self._dibujar_frame()

    def _animar(self):
        if not self.reproduciendo:
            return
        if self.paso_actual < len(self.frames):
            self.paso_actual += 1
            self._dibujar_frame()
            delay = max(80, int(self.var_intervalo.get()))
            self.anim_id = self.after(delay, self._animar)
        else:
            self.pausar()

    def _construir_frames(self):
        """Incluye el punto inicial t=0 y cada paso de Newton-Raphson."""
        altura, pasos = self.model.altura_e_iteraciones()
        if not pasos:
            return altura, []

        R = self.model.radio
        _, g, g_prima = funciones_newton(self.model.volumen, self.model.diametro, self.model.longitud)
        t0 = 0.0
        frames = [
            {
                "t": t0,
                "g": g(t0),
                "g_prima": g_prima(t0),
                "t_nuevo": pasos[0]["t"] if pasos else t0,
                "altura_parcial": R * math.sin(t0) + R,
                "inicial": True,
            }
        ]
        for paso in pasos:
            frames.append({**paso, "inicial": False})
        return altura, frames

    def actualizar(self):
        _, self.frames = self._construir_frames()
        self.iteraciones = self.frames
        if self.paso_actual > len(self.frames):
            self.paso_actual = len(self.frames)
        self._dibujar_frame()

    def _dibujar_frame(self):
        R = self.model.radio
        V = self.model.volumen
        L = self.model.longitud
        _, g, g_prima = funciones_newton(V, self.model.diametro, L)

        t_vals = np.linspace(-math.pi / 2, math.pi / 2, 300)
        g_vals = [g(t) for t in t_vals]

        self.ax_func.clear()
        self.ax_func.plot(t_vals, g_vals, color="#444", lw=1.8, label="g(t)")
        self.ax_func.axhline(0, color="#999", lw=1)
        self.ax_func.set_xlabel("t (rad)")
        self.ax_func.set_ylabel("g(t)")
        self.ax_func.set_title("Función objetivo g(t)")
        self.ax_func.grid(True, alpha=0.3)

        self.ax_alt.clear()
        self.ax_alt.set_title("Altura parcial h(t) = R·sen(t) + R")
        self.ax_alt.set_xlabel("Iteración")
        self.ax_alt.set_ylabel("Altura (m)")
        self.ax_alt.grid(True, alpha=0.3)

        if not self.frames:
            altura, _ = self.model.altura_e_iteraciones()
            self.lbl_estado.config(
                text=f"Volumen = {V:.3f} m³  |  Altura final = {altura:.4f} m  |  (caso límite, sin iteraciones)"
            )
            self.canvas.draw()
            return

        pasos = self.frames[: self.paso_actual]
        for i, it in enumerate(pasos):
            t_i = it["t"]
            g_i = it["g"]
            der = it["g_prima"]
            t_nuevo = it["t_nuevo"]

            color = "#d62728" if i == len(pasos) - 1 else "#ff9896"
            self.ax_func.scatter([t_i], [g_i], color=color, s=50, zorder=5)

            if abs(der) > 1e-12 and not it.get("inicial", False):
                t_line = np.linspace(t_i - 0.5, t_i + 0.5, 2)
                y_line = g_i + der * (t_line - t_i)
                self.ax_func.plot(t_line, y_line, color=color, ls="--", lw=1.3, alpha=0.9)
                self.ax_func.scatter([t_nuevo], [0], color="#2ca02c", s=40, zorder=5, marker="x")

        alturas = [it["altura_parcial"] for it in pasos]
        if alturas:
            self.ax_alt.plot(range(len(alturas)), alturas, "-o", color="#1f77b4", lw=1.5, markersize=5)

        altura_final, _ = self.model.altura_e_iteraciones()
        if alturas:
            self.ax_alt.axhline(altura_final, color="#2ca02c", ls=":", lw=1.2, label=f"h final = {altura_final:.4f} m")
            self.ax_alt.legend(fontsize=8)

        if pasos:
            ultimo = pasos[-1]
            etiqueta = "Inicio" if ultimo.get("inicial") else f"Paso {self.paso_actual}/{len(self.frames)}"
            self.lbl_estado.config(
                text=(
                    f"{etiqueta}  |  t = {ultimo['t']:.6f}  |  g(t) = {ultimo['g']:.2e}  |  "
                    f"h parcial = {ultimo['altura_parcial']:.4f} m  |  "
                    f"Altura final = {altura_final:.4f} m"
                )
            )
        else:
            self.lbl_estado.config(
                text=f"Listo: {len(self.frames)} frames. Presioná Play para ver la convergencia."
            )
        self.canvas.draw()


class AppTanque(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Altura del líquido — Tanque cilíndrico horizontal")
        self.geometry("980x720")
        self.minsize(860, 620)

        self.model = TanqueModel()
        self.model.volumen = self.model.volumen_max * 0.4

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.tab_inicio = PestañaInicio(nb, self.model, self._on_model_change)
        self.tab_parametros = PestañaParametros(nb, self.model, self._on_model_change)
        self.tab_calculos = PestañaCalculos(nb, self.model, self._on_model_change)

        nb.add(self.tab_inicio, text="Inicio")
        nb.add(self.tab_parametros, text="Parámetros")
        nb.add(self.tab_calculos, text="Cálculos")

        self._on_model_change(origen="init")

    def _on_model_change(self, origen=""):
        self.tab_inicio.actualizar()
        self.tab_parametros.actualizar()
        if origen != "calculos":
            self.tab_calculos.pausar()
            self.tab_calculos.paso_actual = 0
            self.tab_calculos.actualizar()


def main():
    app = AppTanque()
    app.mainloop()


if __name__ == "__main__":
    main()

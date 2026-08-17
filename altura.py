import math


def volumen_maximo(D, L):
    """Volumen máximo del tanque cilíndrico horizontal (m³)."""
    R = D / 2.0
    return math.pi * (R ** 2) * L


def funciones_newton(V, D, L):
    """Retorna R y las funciones g(t), g'(t) usadas en Newton-Raphson."""
    R = D / 2.0

    def g(t):
        return (R ** 2 / 2.0) * (math.sin(2 * t) / 2.0 + t + math.pi / 2.0) - (V / (L * 2.0))

    def g_prima(t):
        return (R ** 2 / 2.0) * (math.cos(2 * t) + 1.0)

    return R, g, g_prima


def calcular_altura_liquido(V, D, L, tol=1e-6, max_iter=100):
    """
    Calcula la altura del líquido en un tanque cilíndrico horizontal para cualquier diámetro.
    
    Parámetros:
    V : Volumen del líquido contenido (m^3)
    D : Diámetro del cilindro (m)
    L : Longitud del cilindro (m)
    """
    altura, _ = calcular_altura_con_iteraciones(V, D, L, tol=tol, max_iter=max_iter)
    return altura


def calcular_altura_con_iteraciones(V, D, L, tol=1e-6, max_iter=100):
    """
    Calcula la altura y registra cada paso de Newton-Raphson.

    Retorna (altura, iteraciones) donde cada iteración es un dict con:
    t, g, g_prima, t_nuevo, altura_parcial, convergio
    """
    R = D / 2.0
    V_max = volumen_maximo(D, L)

    """     if V <= 0:
        return 0.0, []
    if V >= V_max:
        return D, [] """

    _, g, g_prima = funciones_newton(V, D, L)
    t = 0.0
    iteraciones = []

    for _ in range(max_iter):
        g_val = g(t)
        g_der = g_prima(t)
        altura_parcial = R * math.sin(t) + R

        if abs(g_der) < 1e-12:
            iteraciones.append(
                {
                    "t": t,
                    "g": g_val,
                    "g_prima": g_der,
                    "t_nuevo": t,
                    "altura_parcial": altura_parcial,
                    "convergio": True,
                }
            )
            break

        t_new = t - g_val / g_der
        t_new = max(-math.pi / 2, min(math.pi / 2, t_new))
        convergio = abs(t_new - t) < tol

        iteraciones.append(
            {
                "t": t,
                "g": g_val,
                "g_prima": g_der,
                "t_nuevo": t_new,
                "altura_parcial": altura_parcial,
                "convergio": convergio,
            }
        )

        if convergio:
            t = t_new
            break

        t = t_new

    altura = R * math.sin(t) + R
    return altura, iteraciones

def testeo():
    print("="*55)
    print("TESTEO DE EXTRAPOLACIÓN DE VOLÚMENES A VARIOS DIÁMETROS")
    print("="*55)
    
    L_test = 10.0 # Longitud constante para las pruebas
    
    # Probaremos con D=2 (Original), D=4 y D=10
    diametros = [2.0, 4.0, 10.0] 
    
    for D in diametros:
        R = D / 2.0
        V_total = math.pi * (R**2) * L_test
        
        print(f"\nTanque -> Diámetro: {D} m | Longitud: {L_test} m | Vol. Total: {V_total:.2f} m³")
        print("-" * 55)
        print(f"{'Escenario':<15} | {'Volumen (m³)':<12} | {'Altura Calculada (m)'}")
        print("-" * 55)
        
        # Casos de prueba por tanque
        casos = [
            ("Vacío (0%)", 0.0),
            ("Un Cuarto (25%)", V_total * 0.25),
            ("Mitad (50%)", V_total * 0.50),
            ("Tres Cua. (75%)", V_total * 0.75),
            ("Lleno (100%)", V_total)
        ]
        
        for nombre, volumen in casos:
            altura = calcular_altura_liquido(volumen, D, L_test)
            print(f"{nombre:<15} | {volumen:<12.2f} | {altura:.4f} m")

if __name__ == "__main__":
    testeo()

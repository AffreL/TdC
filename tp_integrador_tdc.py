import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Número de pasos de simulación
ns = 1200
# Puntos de tiempo
t = np.linspace(0, ns, ns+1)

class model(object):
    # Modelo de la pantalla
    Kp = 1.0      # Ganancia del proceso
    taup = 5.0    # Constante de tiempo del proceso
    thetap = 0.5  # Retardo del proceso

class pid(object):
    # Tuning PID
    Kc = 2.0      # Ganancia proporcional
    tauI = 5.0   # Tiempo integral
    tauD = 0.1    # Tiempo derivativo
    sp = []       # Set Point (punto de ajuste)

# Definir el Set Point
sp = np.zeros(ns+1)
sp[50:1000] = 0.5  # Objetivo de brillo relativo del 50% en una escala de 0 a 1
sp[1000:] = 0
pid.sp = sp

# Perturbación de luz ambiental
ambient_light = np.zeros(ns+1)
ambient_light[300:900] = 0.4
                            #np.linspace(0, 0.4, 600)   # Un rayo de luz aumenta el brillo percibido (Caso de Rampa)

def process(L, t, u, Kp, taup):
    # Modelo del proceso para el control del brillo de la pantalla
    # L = brillo actual de la pantalla
    # t = tiempo
    # u = señal de control
    # Kp = ganancia del proceso
    # taup = constante de tiempo del proceso

    # Ecuación diferencial del proceso
    dLdt = -L/taup + Kp/taup * u
    return dLdt

def calc_response(t, xm, xc):
    # Extracción de parámetros del modelo y del PID
    Kp = xm.Kp
    taup = xm.taup
    thetap = xm.thetap
    ns = len(t)-1
    Kc = xc.Kc
    tauI = xc.tauI
    tauD = xc.tauD
    sp = xc.sp
    delta_t = t[1] - t[0]

    # Almacenamiento para valores de salida y error
    op = np.zeros(ns+1)  # Señal de control
    pv = np.zeros(ns+1)  # Variable del proceso (brillo de la pantalla)
    e = np.zeros(ns+1)   # Error
    ie = np.zeros(ns+1)  # Integral del error
    dpv = np.zeros(ns+1) # Derivada de la variable del proceso
    P = np.zeros(ns+1)   # Componente proporcional
    I = np.zeros(ns+1)   # Componente integral
    D = np.zeros(ns+1)   # Componente derivativa


    op_hi = 1.0  # Límite superior de la señal de control
    op_lo = 0.0  # Límite inferior de la señal de control
    ndelay = int(np.ceil(thetap / delta_t))  # Número de pasos de retardo

    for i in range(0, ns):
        e[i] = sp[i] - (pv[i] - ambient_light[i])  # Error basado en el brillo relativo
        if i >= 1:
            dpv[i] = (pv[i] - pv[i-1]) / delta_t  # Derivada de la variable del proceso
            ie[i] = ie[i-1] + e[i] * delta_t      # Integral del error
        P[i] = Kc * e[i]        # Componente proporcional
        I[i] = Kc / tauI * ie[i]# Componente integral
        D[i] = -Kc * tauD * dpv[i]  # Componente derivativa
        op[i] = op[0] + P[i] + I[i] + D[i] # Señal de control en modo automático
        if op[i] > op_hi:
            op[i] = op_hi
            ie[i] -= e[i] * delta_t # Anti-reset windup
        if op[i] < op_lo:
            op[i] = op_lo
            ie[i] -= e[i] * delta_t # Anti-reset windup
        iop = max(0, i - ndelay)
        y = odeint(process, pv[i], [0, delta_t], args=(op[iop], Kp, taup))
        pv[i+1] = y[-1]
    op[ns] = op[ns-1]
    ie[ns] = ie[ns-1]
    P[ns] = P[ns-1]
    I[ns] = I[ns-1]
    D[ns] = D[ns-1]
    return (pv, op, e)  # Retornar brillo de la pantalla, señal de control y error

def plot_response(n, t, pv, op, sp, e):
    plt.figure(n)

    # Gráfico del Set Point y la Variable del Proceso
    plt.subplot(5, 1, 1)
    
    plt.plot(t, sp, 'k-', linewidth=2, label='Set Point (SP)')
    plt.plot(t, pv - ambient_light, 'b--', linewidth=3, label='Brillo Relativo (PV - Luz Ambiente)')
    plt.legend(loc='best')
    plt.ylabel('Brillo Relativo')

    # Gráfico del Brillo de la Pantalla
    plt.subplot(5, 1, 2)
    plt.plot(t, pv, 'b--', linewidth=3, label='Brillo de la Pantalla (PV)')
    plt.legend(loc='best')
    plt.ylabel('Brillo de la Pantalla')

    # Gráfico de la Señal de Control
    plt.subplot(5, 1, 3)
    plt.plot(t, op, 'r:', linewidth=3, label='Señal de Control (OP)')
    plt.legend(loc='best')
    plt.ylabel('Señal de Control')

    # Gráfico de la Luz Ambiental
    plt.subplot(5, 1, 4)
    plt.plot(t, ambient_light, 'm-', linewidth=2, label='Luz Ambiental')
    plt.legend(loc='best')
    plt.ylabel('Luz Ambiental')

    # Gráfico del Error
    plt.subplot(5, 1, 5)
    plt.plot(t, e, 'g-', linewidth=2, label='Error (e)')
    plt.legend(loc='best')
    plt.ylabel('Error')
    plt.xlabel('Tiempo')

    plt.tight_layout()


# Simulación en modo PID
pid.Kc = 2.0
pid.tauI = 5.0
pid.tauD = 0.1

(pv, op, e) = calc_response(t, model, pid)
plot_response("Impulso", t, pv, op, sp, e)

ambient_light = np.zeros(ns+1)
ambient_light[300:900] = np.linspace(0, 0.4, 600)   # Un rayo de luz aumenta el brillo percibido (Caso de Rampa)

(pv, op, e) = calc_response(t, model, pid)
plot_response("Rampa", t, pv, op, sp, e)

plt.show()

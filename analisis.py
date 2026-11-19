"""
MÓDULO DE ANÁLISIS MICROBIOLÓGICO, ALERTAS MDR Y TENDENCIAS (analisis.py)
Proyecto: SIGT-LAB (Bioingeniería / Informática 1)
Rol responsable: Integrante 2 (Lógica de negocio y alertas)
Autores del equipo: [completar con los nombres del equipo]

Interpreta la CMI con la tabla de puntos de corte que arma el Integrante 4
(datos/puntos_corte.json), detecta cepas MDR (resistencia a UMBRAL_MDR o más familias)
y calcula la tendencia del crecimiento según las horas de incubación.
"""

import json
import math
import os

try:
    from config import UMBRAL_MDR
except ImportError:
    UMBRAL_MDR = 3

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_PUNTOS_CORTE = os.path.join(CARPETA_BASE, "datos", "puntos_corte.json")

# Supuesto a confirmar con el equipo: si el conteo cambia menos que este valor
# (en log10 UFC/mL por hora), la tendencia se considera estable.
UMBRAL_ESTABLE_LOG10_POR_HORA = 0.05

# Escala ordinal para crecimiento reportado en texto
ESCALA_CRECIMIENTO = [("sin crecimiento", 0), ("escaso", 1), ("moderado", 2), ("abundante", 3)]

_tabla_en_memoria = None


# ---------------------------------------------------------------------
# Tabla de puntos de corte (la arma el Integrante 4)
# ---------------------------------------------------------------------
def cargar_tabla_puntos_corte(ruta=ARCHIVO_PUNTOS_CORTE):
    """
    Lee la tabla de puntos de corte (CLSI/EUCAST) desde un JSON.

    Formato por antibiótico:
        {"familia": str, "sensible_max": float, "resistente_min": float, "fuente": str}

    Retorna:
        dict: Tabla con el nombre del antibiótico como llave.
    Lanza:
        FileNotFoundError si no existe el archivo; ValueError si una entrada está incompleta.
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"No se encontró la tabla de puntos de corte en '{ruta}'. Solicítela al Integrante 4."
        )

    with open(ruta, mode="r", encoding="utf-8") as archivo:
        tabla = json.load(archivo)

    for antibiotico, corte in tabla.items():
        faltantes = [campo for campo in ("familia", "sensible_max", "resistente_min") if campo not in corte]
        if faltantes:
            raise ValueError(f"El antibiótico '{antibiotico}' no tiene los campos: {', '.join(faltantes)}.")
        if float(corte["sensible_max"]) >= float(corte["resistente_min"]):
            raise ValueError(f"En '{antibiotico}', sensible_max debe ser menor que resistente_min.")

    return tabla


def obtener_tabla_puntos_corte():
    """Carga la tabla una sola vez y la reutiliza en las siguientes llamadas."""
    global _tabla_en_memoria
    if _tabla_en_memoria is None:
        _tabla_en_memoria = cargar_tabla_puntos_corte()
    return _tabla_en_memoria


def _buscar_corte(antibiotico, catalogo):
    """Busca un antibiótico sin distinguir mayúsculas ni espacios. Retorna None si no existe."""
    clave = str(antibiotico).strip().lower()
    for nombre, corte in catalogo.items():
        if nombre.strip().lower() == clave:
            return corte
    return None


# ---------------------------------------------------------------------
# Interpretación de CMI
# ---------------------------------------------------------------------
def interpretar_cmi(antibiotico, cmi, tabla_corte=None):
    """
    Clasifica una CMI (ug/mL) como 'Sensible', 'Intermedio' o 'Resistente'.

    Parámetros:
        antibiotico (str): Nombre del antibiótico.
        cmi (float | int | str): Valor de la CMI, mayor que 0.
        tabla_corte (dict, opcional): Tabla alterna. Si no se da, usa datos/puntos_corte.json.

    Retorna:
        str: 'Sensible', 'Intermedio' o 'Resistente'.
    Lanza:
        ValueError si la CMI no es válida; KeyError si el antibiótico no está en la tabla.
    """
    try:
        valor_cmi = float(cmi)
    except (TypeError, ValueError):
        raise ValueError(f"El valor de CMI ('{cmi}') debe ser un número válido.")

    if math.isnan(valor_cmi) or valor_cmi <= 0:
        raise ValueError("El valor de la CMI debe ser mayor que 0 ug/mL.")

    catalogo = tabla_corte if tabla_corte is not None else obtener_tabla_puntos_corte()
    corte = _buscar_corte(antibiotico, catalogo)
    if corte is None:
        raise KeyError(f"El antibiótico '{antibiotico}' no está en la tabla de puntos de corte.")

    if valor_cmi <= float(corte["sensible_max"]):
        return "Sensible"
    if valor_cmi >= float(corte["resistente_min"]):
        return "Resistente"
    return "Intermedio"


def obtener_familia_antibiotico(antibiotico, tabla_corte=None):
    """
    Devuelve la familia antimicrobiana del antibiótico, o 'Desconocida' si no está en la tabla.
    """
    catalogo = tabla_corte if tabla_corte is not None else obtener_tabla_puntos_corte()
    corte = _buscar_corte(antibiotico, catalogo)
    return corte["familia"] if corte else "Desconocida"


# ---------------------------------------------------------------------
# Detección MDR
# ---------------------------------------------------------------------
def detectar_mdr(antibiogramas):
    """
    Indica si el cultivo es Multidrogoresistente (MDR): resistencia a UMBRAL_MDR o más familias.

    Parámetros:
        antibiogramas (list[dict]): Cada dict trae 'antibiotico' y 'interpretacion' o 'cmi_ug_ml'.
            'familia' es opcional; si falta, se toma de la tabla de puntos de corte.

    Retorna:
        dict: 'es_mdr', 'familias_resistentes', 'total_familias' y 'mensaje_alerta'.
    Lanza:
        TypeError si el parámetro no es una lista.
    """
    if not isinstance(antibiogramas, list):
        raise TypeError("El parámetro 'antibiogramas' debe ser una lista de diccionarios.")

    familias_resistentes = set()

    for item in antibiogramas:
        interpretacion = str(item.get("interpretacion", "")).strip().capitalize()

        if not interpretacion and "antibiotico" in item and "cmi_ug_ml" in item:
            interpretacion = interpretar_cmi(item["antibiotico"], item["cmi_ug_ml"])

        if interpretacion == "Resistente":
            familia = (item.get("familia") or obtener_familia_antibiotico(item.get("antibiotico", ""))).strip()
            # Una familia desconocida no se cuenta; conviene revisar la tabla si aparece
            if familia and familia != "Desconocida":
                familias_resistentes.add(familia)

    lista_familias = sorted(familias_resistentes)
    es_mdr = len(lista_familias) >= UMBRAL_MDR

    if es_mdr:
        mensaje = (
            f"[ALERTA EPIDEMIOLÓGICA MDR]: Cepa Multidrogoresistente detectada. "
            f"Resistente a {len(lista_familias)} familias: {', '.join(lista_familias)}."
        )
    else:
        mensaje = (
            f"Cultivo sin alerta MDR ({len(lista_familias)} familia(s) resistente(s), "
            f"umbral requerido: {UMBRAL_MDR})."
        )

    return {
        "es_mdr": es_mdr,
        "familias_resistentes": lista_familias,
        "total_familias": len(lista_familias),
        "mensaje_alerta": mensaje,
    }


# ---------------------------------------------------------------------
# Tendencia de crecimiento frente a horas de incubación
# ---------------------------------------------------------------------
def _a_numero(valor):
    """Convierte a float; retorna None si no es numérico."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _nivel_crecimiento(texto):
    """Convierte un crecimiento en texto a su nivel ordinal (0 a 3)."""
    minusculas = str(texto).lower()
    for palabra, nivel in ESCALA_CRECIMIENTO:
        if palabra in minusculas:
            return nivel
    raise ValueError(
        f"No se reconoce el crecimiento '{texto}'. Use 'sin crecimiento', 'escaso', "
        f"'moderado', 'abundante' o un conteo en UFC/mL."
    )


def _clasificar_tiempo(horas):
    """Clasifica la hora de lectura según el tiempo de incubación."""
    if horas < 24:
        return "Crecimiento rápido (fase exponencial temprana < 24 h)"
    if horas <= 48:
        return "Crecimiento estándar (24 h - 48 h)"
    return "Crecimiento lento o microorganismo fastidioso (> 48 h)"


def calcular_tendencia(horas, crecimiento):
    """
    Relaciona las horas de incubación con el crecimiento y determina si el cultivo sube,
    se mantiene o baja.

    Parámetros:
        horas (float | list): Horas de incubación de cada medición (mayores a 0).
        crecimiento (float | str | list): Conteo en UFC/mL, o nivel en texto
            ('sin crecimiento', 'escaso', 'moderado', 'abundante'). Si es lista,
            debe tener la misma longitud que horas.

    Retorna:
        dict: 'horas_evaluadas', 'crecimiento_reportado', 'tipo_dato', 'tendencia',
              'velocidad_log10_por_hora' (None si es categórico o hay una sola medición),
              'clasificacion_tiempo' y 'resumen'.
    Lanza:
        ValueError si los datos son inconsistentes.
    """
    if not isinstance(horas, list):
        horas = [horas]
    if not isinstance(crecimiento, list):
        crecimiento = [crecimiento]
    if not horas or len(horas) != len(crecimiento):
        raise ValueError("Debe haber la misma cantidad de horas y de mediciones de crecimiento, y al menos una.")

    horas_numericas = [_a_numero(h) for h in horas]
    if any(h is None or h <= 0 for h in horas_numericas):
        raise ValueError("Las horas de incubación deben ser números mayores a 0.")

    mediciones = sorted(zip(horas_numericas, crecimiento), key=lambda m: m[0])

    conteos = [_a_numero(c) for _, c in mediciones]
    if all(c is not None for c in conteos):
        if any(c <= 0 for c in conteos):
            raise ValueError("Los conteos en UFC/mL deben ser mayores que 0.")
        serie = [(h, math.log10(c)) for (h, _), c in zip(mediciones, conteos)]
        tipo = "numerico (UFC/mL)"
    else:
        serie = [(h, _nivel_crecimiento(c)) for h, c in mediciones]
        tipo = "categorico"

    hora_final, valor_final = mediciones[-1]

    if len(serie) < 2 or serie[0][0] == serie[-1][0]:
        tendencia = "No determinable (se necesitan al menos 2 mediciones en horas distintas)"
        velocidad = None
    else:
        (h0, v0), (h1, v1) = serie[0], serie[-1]
        if tipo.startswith("numerico"):
            velocidad = (v1 - v0) / (h1 - h0)
            if abs(velocidad) < UMBRAL_ESTABLE_LOG10_POR_HORA:
                tendencia = "Estable"
            else:
                tendencia = "Ascendente" if velocidad > 0 else "Descendente"
        else:
            velocidad = None
            diferencia = v1 - v0
            if diferencia == 0:
                tendencia = "Estable"
            else:
                tendencia = "Ascendente" if diferencia > 0 else "Descendente"

    horas_finales = round(hora_final, 2)
    clasificacion = _clasificar_tiempo(hora_final)
    texto_velocidad = f", variación de {velocidad:+.3f} log10 UFC/mL por hora" if velocidad is not None else ""

    return {
        "horas_evaluadas": horas_finales,
        "crecimiento_reportado": valor_final,
        "tipo_dato": tipo,
        "tendencia": tendencia,
        "velocidad_log10_por_hora": round(velocidad, 3) if velocidad is not None else None,
        "clasificacion_tiempo": clasificacion,
        "resumen": f"A las {horas_finales} h: crecimiento {tendencia.lower()}{texto_velocidad}. {clasificacion}.",
    }


# =====================================================================
# BLOQUE DE PRUEBA MANUAL (python analisis.py)
# =====================================================================
if __name__ == "__main__":
    print("=== PRUEBAS DEL MÓDULO ANALISIS.PY (SIGT-LAB) ===\n")

    print("--- PRUEBA 1: Interpretación de CMI ---")
    for antib, valor in [("Ceftazidima", 64.0), ("Ciprofloxacina", 1.0), ("Meropenem", 0.5)]:
        print(f"{antib:15} CMI {valor:5} ug/mL -> {interpretar_cmi(antib, valor)}")

    print("\n--- PRUEBA 2: Caso UCI (3 familias resistentes) ---")
    caso_uci = [
        {"antibiotico": "Ceftazidima", "cmi_ug_ml": 64.0},
        {"antibiotico": "Ciprofloxacina", "cmi_ug_ml": 4.0},
        {"antibiotico": "Meropenem", "cmi_ug_ml": 16.0},
    ]
    print(detectar_mdr(caso_uci)["mensaje_alerta"])

    print("\n--- PRUEBA 3: Caso con 1 sola familia resistente ---")
    caso_normal = [
        {"antibiotico": "Ceftazidima", "cmi_ug_ml": 64.0},
        {"antibiotico": "Ciprofloxacina", "cmi_ug_ml": 0.25},
        {"antibiotico": "Meropenem", "cmi_ug_ml": 1.0},
    ]
    print(detectar_mdr(caso_normal)["mensaje_alerta"])

    print("\n--- PRUEBA 4: Tendencia con conteos en UFC/mL ---")
    print(calcular_tendencia([6, 12, 18], [1e3, 1e5, 1e7])["resumen"])

    print("\n--- PRUEBA 5: Tendencia con niveles de texto ---")
    print(calcular_tendencia([6, 18], ["escaso", "abundante"])["resumen"])

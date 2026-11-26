"""
MÓDULO DE ANÁLISIS MICROBIOLÓGICO, ALERTAS MDR Y TENDENCIAS (analisis.py)
Proyecto: SIGT-LAB (Bioingeniería / Informática 1)
Rol responsable: Integrante 2 (Lógica de negocio y alertas)
Autores del equipo: Julián, Ana, Valeria, Emmanuel

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

# Campos obligatorios de cada punto de corte. Sirven también para distinguir
# una entrada plana de un bloque organizado por microorganismo.
CAMPOS_PUNTO_CORTE = ("familia", "sensible_max", "resistente_min")

# Supuesto a confirmar con el equipo: si el conteo cambia menos que este valor
# (en log10 UFC/mL por hora), la tendencia se considera estable.
UMBRAL_ESTABLE_LOG10_POR_HORA = 0.05

# Escala ordinal para crecimiento reportado en texto
ESCALA_CRECIMIENTO = [("sin crecimiento", 0), ("escaso", 1), ("moderado", 2), ("abundante", 3)]

_tabla_en_memoria = None


# ---------------------------------------------------------------------
# Resolución de rutas de archivos de datos
# ---------------------------------------------------------------------
def _resolver_ruta(nombre_archivo):
    """
    Devuelve la ruta real de un archivo de datos.

    Busca primero en <carpeta_del_script>/datos/<nombre_archivo> y, si no existe
    ahí, en <carpeta_del_script>/<nombre_archivo>. Si ninguna de las dos existe,
    devuelve la ruta dentro de 'datos'.

    Retorna:
        str: Ruta absoluta del archivo.
    """
    ruta_en_datos = os.path.join(CARPETA_BASE, "datos", nombre_archivo)
    if os.path.exists(ruta_en_datos):
        return ruta_en_datos
    ruta_en_base = os.path.join(CARPETA_BASE, nombre_archivo)
    if os.path.exists(ruta_en_base):
        return ruta_en_base
    return ruta_en_datos


ARCHIVO_PUNTOS_CORTE = _resolver_ruta("puntos_corte.json")


# ---------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------
def _normalizar(texto):
    """Pasa a minúsculas y colapsa espacios. Permite comparar nombres sin importar formato."""
    return " ".join(str(texto).split()).lower()


def _es_bloque_por_microorganismo(valor):
    """
    True si el valor del catálogo es un bloque {antibiotico: {...}} de un microorganismo.
    Una entrada plana de antibiótico siempre trae al menos uno de los CAMPOS_PUNTO_CORTE.
    """
    return isinstance(valor, dict) and not any(campo in valor for campo in CAMPOS_PUNTO_CORTE)


def _validar_finito(valor, descripcion):
    """Rechaza inf, -inf y nan con un ValueError claro."""
    if not math.isfinite(valor):
        raise ValueError(
            f"Valor no válido en {descripcion} ({valor}): no se admiten inf, -inf ni nan."
        )


def _a_numero(valor):
    """Convierte a float; retorna None si no es numérico."""
    if isinstance(valor, bool):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------
# Tabla de puntos de corte (la arma el Integrante 4)
# ---------------------------------------------------------------------
def _validar_punto_corte(nombre, corte):
    """Valida una entrada de antibiótico. Lanza ValueError si está incompleta o es inconsistente."""
    if not isinstance(corte, dict):
        raise ValueError(f"La entrada '{nombre}' debe ser un diccionario.")
    faltantes = [campo for campo in CAMPOS_PUNTO_CORTE if campo not in corte]
    if faltantes:
        raise ValueError(f"El antibiótico '{nombre}' no tiene los campos: {', '.join(faltantes)}.")
    if float(corte["sensible_max"]) >= float(corte["resistente_min"]):
        raise ValueError(f"En '{nombre}', sensible_max debe ser menor que resistente_min.")


def cargar_tabla_puntos_corte(ruta=ARCHIVO_PUNTOS_CORTE):
    """
    Lee la tabla de puntos de corte (CLSI/EUCAST) desde un JSON.

    Formato plano (actual) por antibiótico:
        {"familia": str, "sensible_max": float, "resistente_min": float, "fuente": str,
         "microorganismo": str (opcional)}

    Formato por microorganismo (opcional), anidado por microorganismo:
        {"Escherichia coli": {"Ceftazidima": {...}}, "Ceftazidima": {...}}

    Retorna:
        dict: Tabla con el nombre del antibiótico (o del microorganismo) como llave.
    Lanza:
        FileNotFoundError si no existe el archivo; ValueError si una entrada está incompleta.
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"No se encontró la tabla de puntos de corte en '{ruta}'. Solicítela al Integrante 4."
        )

    with open(ruta, mode="r", encoding="utf-8") as archivo:
        tabla = json.load(archivo)

    for nombre, valor in tabla.items():
        if _es_bloque_por_microorganismo(valor):
            for antibiotico, corte in valor.items():
                _validar_punto_corte(f"{nombre} / {antibiotico}", corte)
        else:
            _validar_punto_corte(nombre, valor)

    return tabla


def obtener_tabla_puntos_corte():
    """Carga la tabla una sola vez y la reutiliza en las siguientes llamadas."""
    global _tabla_en_memoria
    if _tabla_en_memoria is None:
        _tabla_en_memoria = cargar_tabla_puntos_corte()
    return _tabla_en_memoria


def _buscar_en_plano(clave, catalogo, clave_microorganismo):
    """
    Busca un antibiótico en el nivel plano del catálogo.
    Una entrada sin campo 'microorganismo' aplica a cualquier microorganismo.
    Una entrada con ese campo solo aplica si coincide con el microorganismo pedido.
    """
    generico = None
    for nombre, corte in catalogo.items():
        if _es_bloque_por_microorganismo(corte) or _normalizar(nombre) != clave:
            continue
        micro_entrada = corte.get("microorganismo")
        if micro_entrada:
            if clave_microorganismo and _normalizar(micro_entrada) == clave_microorganismo:
                return corte
        elif generico is None:
            generico = corte
    return generico


def _buscar_corte(antibiotico, catalogo, microorganismo=None):
    """
    Busca el punto de corte de un antibiótico sin distinguir mayúsculas ni espacios.

    Orden de búsqueda:
        1. Si se pide microorganismo y existe un bloque con ese nombre, se busca dentro de él.
        2. Si no, se busca en el nivel plano (entradas generales o marcadas con ese microorganismo).

    Retorna None si no existe.
    """
    clave = _normalizar(antibiotico)
    clave_microorganismo = _normalizar(microorganismo) if microorganismo else None

    if clave_microorganismo:
        for nombre_micro, bloque in catalogo.items():
            if _es_bloque_por_microorganismo(bloque) and _normalizar(nombre_micro) == clave_microorganismo:
                corte = _buscar_en_plano(clave, bloque, None)
                if corte is not None:
                    return corte

    return _buscar_en_plano(clave, catalogo, clave_microorganismo)


# ---------------------------------------------------------------------
# Interpretación de CMI
# ---------------------------------------------------------------------
def interpretar_cmi(antibiotico, cmi, tabla_corte=None, microorganismo=None):
    """
    Clasifica una CMI (ug/mL) como 'Sensible', 'Intermedio' o 'Resistente'.

    Parámetros:
        antibiotico (str): Nombre del antibiótico.
        cmi (float | int | str): Valor de la CMI, finito y mayor que 0.
        tabla_corte (dict, opcional): Tabla alterna. Si no se da, usa datos/puntos_corte.json.
        microorganismo (str, opcional): Si la tabla tiene puntos de corte por microorganismo,
            se usan los de ese microorganismo. Si no se encuentran, se usa el punto general.

    Retorna:
        str: 'Sensible', 'Intermedio' o 'Resistente'.
    Lanza:
        ValueError si la CMI no es válida (no numérica, inf, -inf, nan o <= 0);
        KeyError si el antibiótico no está en la tabla.
    """
    if isinstance(cmi, bool):
        raise ValueError(f"El valor de CMI ('{cmi}') debe ser un número válido.")
    try:
        valor_cmi = float(cmi)
    except (TypeError, ValueError):
        raise ValueError(f"El valor de CMI ('{cmi}') debe ser un número válido.")

    if not math.isfinite(valor_cmi) or valor_cmi <= 0:
        raise ValueError("El valor de la CMI debe ser un número finito mayor que 0 ug/mL.")

    catalogo = tabla_corte if tabla_corte is not None else obtener_tabla_puntos_corte()
    corte = _buscar_corte(antibiotico, catalogo, microorganismo)
    if corte is None:
        raise KeyError(f"El antibiótico '{antibiotico}' no está en la tabla de puntos de corte.")

    if valor_cmi <= float(corte["sensible_max"]):
        return "Sensible"
    if valor_cmi >= float(corte["resistente_min"]):
        return "Resistente"
    return "Intermedio"


def obtener_familia_antibiotico(antibiotico, tabla_corte=None, microorganismo=None):
    """
    Devuelve la familia antimicrobiana del antibiótico, o 'Desconocida' si no está en la tabla.
    Lanza FileNotFoundError si la tabla no existe y no se pasó tabla_corte.
    """
    catalogo = tabla_corte if tabla_corte is not None else obtener_tabla_puntos_corte()
    corte = _buscar_corte(antibiotico, catalogo, microorganismo)
    return corte["familia"] if corte else "Desconocida"


# ---------------------------------------------------------------------
# Detección MDR
# ---------------------------------------------------------------------
def detectar_mdr(antibiogramas):
    """
    Indica si el cultivo es Multidrogoresistente (MDR): resistencia a UMBRAL_MDR o más familias.

    Regla operativa del equipo para el conteo MDR:
        - Solo los resultados 'Resistente' suman al conteo.
        - Los 'Intermedio' no suman.
        - Los datos faltantes (sin interpretación ni CMI válida) no suman y generan advertencia.
        - Una familia repetida cuenta una sola vez (sin distinguir mayúsculas ni espacios).

    Campo de familia: se lee primero 'familia' y luego 'familia_antibiotico' (formato de
    crud_mysql.py). Solo si ambos están vacíos se consulta la tabla de puntos de corte.
    Si la tabla no existe, el antibiótico no cuenta y queda una advertencia en el resultado.

    Parámetros:
        antibiogramas (list[dict]): Cada dict trae 'antibiotico' y 'interpretacion' o 'cmi_ug_ml'.
            Opcionalmente 'familia' o 'familia_antibiotico' y 'microorganismo'.

    Retorna:
        dict: 'es_mdr', 'familias_resistentes', 'total_familias', 'mensaje_alerta'
              y 'advertencias' (lista de textos; vacía si no hubo problemas).
    Lanza:
        TypeError si el parámetro no es una lista.
    """
    if not isinstance(antibiogramas, list):
        raise TypeError("El parámetro 'antibiogramas' debe ser una lista de diccionarios.")

    familias = {}  # clave normalizada -> nombre para mostrar
    advertencias = []

    for item in antibiogramas:
        interpretacion = str(item.get("interpretacion") or "").strip().capitalize()
        cmi_val = item.get("cmi_ug_ml")

        if not interpretacion:
            if item.get("antibiotico") and cmi_val is not None and str(cmi_val).strip() != "":
                try:
                    interpretacion = interpretar_cmi(
                        item["antibiotico"], cmi_val, microorganismo=item.get("microorganismo")
                    )
                except (FileNotFoundError, KeyError, ValueError) as error_cmi:
                    advertencias.append(
                        f"No se pudo interpretar '{item.get('antibiotico', '?')}' "
                        f"(CMI={cmi_val}): {error_cmi}"
                    )
                    continue
            else:
                advertencias.append(
                    f"Dato incompleto para '{item.get('antibiotico', '?')}': "
                    f"sin interpretación ni CMI válida; no cuenta para MDR."
                )
                continue

        if interpretacion != "Resistente":
            continue

        familia = str(item.get("familia") or item.get("familia_antibiotico") or "").strip()
        if not familia:
            try:
                familia = obtener_familia_antibiotico(
                    item.get("antibiotico", ""), microorganismo=item.get("microorganismo")
                ).strip()
            except FileNotFoundError as error_tabla:
                advertencias.append(
                    f"No se pudo determinar la familia de '{item.get('antibiotico', '?')}' "
                    f"y no cuenta para MDR: {error_tabla}"
                )
                continue

        if not familia or familia == "Desconocida":
            advertencias.append(
                f"El antibiótico '{item.get('antibiotico', '?')}' no tiene familia en la tabla "
                f"y no cuenta para MDR. Revisar puntos de corte."
            )
            continue

        familias.setdefault(_normalizar(familia), familia)

    lista_familias = sorted(familias.values())
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
        "advertencias": advertencias,
    }


# ---------------------------------------------------------------------
# Tendencia de crecimiento frente a horas de incubación
# ---------------------------------------------------------------------
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
        horas (float | list): Horas de incubación de cada medición (finitas y mayores a 0).
        crecimiento (float | str | list): Conteo en UFC/mL (finito y mayor a 0), o nivel en
            texto ('sin crecimiento', 'escaso', 'moderado', 'abundante'). Si es lista,
            debe tener la misma longitud que horas.

    Retorna:
        dict: 'horas_evaluadas', 'crecimiento_reportado', 'tipo_dato', 'tendencia',
              'velocidad_log10_por_hora' (None si es categórico o hay una sola medición),
              'clasificacion_tiempo' y 'resumen'.
    Lanza:
        ValueError si los datos son inconsistentes o contienen inf, -inf o nan.
    """
    if not isinstance(horas, list):
        horas = [horas]
    if not isinstance(crecimiento, list):
        crecimiento = [crecimiento]
    if not horas or len(horas) != len(crecimiento):
        raise ValueError("Debe haber la misma cantidad de horas y de mediciones de crecimiento, y al menos una.")

    horas_numericas = []
    for h in horas:
        valor = _a_numero(h)
        if valor is None:
            raise ValueError(f"La hora de incubación '{h}' debe ser un número.")
        _validar_finito(valor, "horas de incubación")
        if valor <= 0:
            raise ValueError("Las horas de incubación deben ser números mayores a 0.")
        horas_numericas.append(valor)

    mediciones = sorted(zip(horas_numericas, crecimiento), key=lambda m: m[0])

    conteos = [_a_numero(c) for _, c in mediciones]
    if all(c is not None for c in conteos):
        for c in conteos:
            _validar_finito(c, "conteos en UFC/mL")
            if c <= 0:
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

    print("\n--- PRUEBA 6: MDR con llave 'familia_antibiotico' (formato crud_mysql.py) ---")
    filas_mysql = [
        {"antibiotico": "Ceftazidima", "familia_antibiotico": "Cefalosporinas", "interpretacion": "Resistente"},
        {"antibiotico": "Ciprofloxacina", "familia_antibiotico": "Fluoroquinolonas", "interpretacion": "Resistente"},
        {"antibiotico": "Meropenem", "familia_antibiotico": "Carbapenemicos", "interpretacion": "Resistente"},
        {"antibiotico": "Gentamicina", "familia_antibiotico": "Aminoglucosidos", "interpretacion": "Intermedio"},
    ]
    resultado_mysql = detectar_mdr(filas_mysql)
    assert resultado_mysql["es_mdr"] is True, "Debe ser MDR con 3 familias resistentes"
    assert resultado_mysql["total_familias"] == 3, "Solo deben contar las 3 familias Resistente"
    assert "Aminoglucosidos" not in resultado_mysql["familias_resistentes"], "Intermedio no debe contar"
    print("[OK]", resultado_mysql["mensaje_alerta"])

    print("\n--- PRUEBA 7: Datos incompletos no rompen detectar_mdr ---")
    caso_incompleto = [
        {"antibiotico": "Ceftazidima", "cmi_ug_ml": None},
        {"antibiotico": "AntibioticoInexistente", "cmi_ug_ml": 8.0},
    ]
    res_incompleto = detectar_mdr(caso_incompleto)
    assert res_incompleto["es_mdr"] is False
    assert len(res_incompleto["advertencias"]) == 2
    print("[OK] Advertencias controladas:", len(res_incompleto["advertencias"]))

    print("\n--- PRUEBA 8: Entradas inválidas lanzan ValueError ---")
    casos_invalidos = [
        ("CMI inf", interpretar_cmi, ("Ceftazidima", float("inf"))),
        ("CMI -inf", interpretar_cmi, ("Ceftazidima", float("-inf"))),
        ("CMI nan", interpretar_cmi, ("Ceftazidima", float("nan"))),
        ("CMI igual a 0", interpretar_cmi, ("Ceftazidima", 0)),
        ("CMI negativa", interpretar_cmi, ("Ceftazidima", -2)),
        ("Hora inf en tendencia", calcular_tendencia, ([float("inf"), 12], [1e3, 1e5])),
        ("Conteo nan en tendencia", calcular_tendencia, ([6, 12], [float("nan"), 1e5])),
    ]
    for nombre, funcion, argumentos in casos_invalidos:
        try:
            funcion(*argumentos)
        except ValueError:
            print(f"[OK] {nombre} -> ValueError")
        else:
            raise AssertionError(f"{nombre} debió lanzar ValueError")

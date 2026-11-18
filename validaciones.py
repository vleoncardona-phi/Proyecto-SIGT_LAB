# =====================================================================
# Módulo avanzado de validación y sanitización defensiva con try/except
# para todas las entradas del sistema (enteros, CMI, fechas, opciones).
# =====================================================================

import datetime


def validar_entero(valor, campo="Campo", minimo=0, maximo=120):
    """
    Convierte 'valor' a entero y verifica que esté en el rango [minimo, maximo].
    Maneja ValueError con mensajes descriptivos.
    """
    try:
        numero = int(str(valor).strip())
    except (ValueError, TypeError):
        raise ValueError(f"'{valor}' no es un número entero válido.")

    if not (minimo <= numero <= maximo):
        raise ValueError(f"El valor de {campo} debe estar entre {minimo} y {maximo}.")

    return numero


def validar_flotante(valor, campo="Campo", minimo=0.0, maximo=None):
    """
    Convierte 'valor' a float (ej: CMI o temperatura) y verifica los límites.
    """
    try:
        numero = float(str(valor).strip())
    except (ValueError, TypeError):
        raise ValueError(f"'{valor}' no es un número decimal válido.")

    if numero < minimo:
        raise ValueError(f"El campo {campo} debe ser mayor o igual a {minimo}.")

    if maximo is not None and numero > maximo:
        raise ValueError(f"El campo {campo} no puede ser mayor a {maximo}.")

    return numero


def validar_texto(valor, campo="Campo", min_len=1, max_len=255):
    """
    Sanea y valida que una cadena no esté vacía ni supere el tamaño permitido.
    """
    if valor is None:
        raise ValueError(f"El campo {campo} no puede ser nulo.")

    texto = str(valor).strip()
    if len(texto) < min_len:
        raise ValueError(f"El campo {campo} no puede estar vacío.")

    if len(texto) > max_len:
        raise ValueError(f"El campo {campo} supera los {max_len} caracteres permitidos.")

    return texto


def validar_fecha(valor, campo="Fecha", formato="%Y-%m-%d"):
    """
    Valida que la fecha tenga el formato especificado (ej. AAAA-MM-DD) y sea una fecha real en el calendario.
    Detecta automáticamente fechas imposibles como 31/02.
    """
    texto = str(valor).strip()
    try:
        fecha_dt = datetime.datetime.strptime(texto, formato)
        return fecha_dt.strftime(formato)
    except ValueError:
        raise ValueError(f"La fecha '{texto}' no es válida o es una fecha imposible (formato requerido: AAAA-MM-DD).")


def validar_opcion(valor, opciones_validas, campo="Opción"):
    """
    Valida que el valor ingresado corresponda a una de las opciones válidas permitidas.
    """
    opcion_str = str(valor).strip()
    opciones_str = [str(op).strip() for op in opciones_validas]

    if opcion_str not in opciones_str:
        lista_fmt = ", ".join(opciones_str)
        raise ValueError(f"Opción '{opcion_str}' no válida. Opciones disponibles: [{lista_fmt}].")

    return opcion_str


def pedir_dato_interactivo(mensaje, funcion_validacion, *args, **kwargs):
    """
    Solicita una entrada por teclado repetidamente hasta que cumpla la validación,
    evitando cierres abruptos de la aplicación por excepciones no capturadas.
    """
    while True:
        try:
            entrada = input(mensaje)
            return funcion_validacion(entrada, *args, **kwargs)
        except ValueError as err:
            print(f"Error de validación: {err} Intente de nuevo.\n")

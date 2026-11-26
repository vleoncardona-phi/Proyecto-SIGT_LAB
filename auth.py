"""
MÓDULO DE AUTENTICACIÓN (auth.py)
Proyecto: SIGT-LAB (Bioingeniería / Informática 1)
Rol responsable: Integrante 2 (Lógica de negocio y alertas)
Autores del equipo: Julián, Ana, Valeria, Emmanuel

Valida usuario y clave contra datos/usuarios_credenciales.csv (clave en hash PBKDF2),
bloquea la cuenta tras MAX_INTENTOS fallos seguidos (contador guardado en el CSV),
registra cada intento en datos/log_accesos.txt y consulta el rol en MySQL
(tablas 'administradores' y 'usuarios', según esquema_mysql.sql).
"""

import csv
import hashlib
import hmac
import os
import secrets
from datetime import datetime

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_DATOS = os.path.join(CARPETA_BASE, "datos")

MAX_INTENTOS = 3
ITERACIONES_HASH = 100_000
COLUMNAS_CSV = ["id_usuario", "username", "password_hash", "ultimo_acceso", "intentos_fallidos"]
PERMISOS_POR_ROL = {
    "Administrador": "CRUD_TOTAL",
    "Bacteriologo": "REGISTRO_Y_LECTURA",
}


# ---------------------------------------------------------------------
# Resolución de rutas de archivos de datos
# ---------------------------------------------------------------------
def _resolver_ruta(nombre_archivo):
    """
    Devuelve la ruta real de un archivo de datos.

    Busca primero en <carpeta_del_script>/datos/<nombre_archivo> y, si no existe
    ahí, en <carpeta_del_script>/<nombre_archivo>. Si ninguna de las dos existe,
    devuelve la ruta dentro de 'datos', que es donde se creará el archivo.

    Retorna:
        str: Ruta absoluta del archivo.
    """
    ruta_en_datos = os.path.join(CARPETA_DATOS, nombre_archivo)
    if os.path.exists(ruta_en_datos):
        return ruta_en_datos
    ruta_en_base = os.path.join(CARPETA_BASE, nombre_archivo)
    if os.path.exists(ruta_en_base):
        return ruta_en_base
    return ruta_en_datos


ARCHIVO_CREDENCIALES = _resolver_ruta("usuarios_credenciales.csv")
ARCHIVO_LOG = _resolver_ruta("log_accesos.txt")


# ---------------------------------------------------------------------
# Hash de contraseñas (biblioteca estándar, sin dependencias externas)
# ---------------------------------------------------------------------
def generar_hash(clave):
    """
    Crea un hash PBKDF2-HMAC-SHA256 con sal aleatoria.

    Retorna:
        str: Cadena 'sal$hash', lista para guardar en el CSV.
    """
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal.encode("utf-8"), ITERACIONES_HASH)
    return f"{sal}${digest.hex()}"


def verificar_hash(clave, hash_guardado):
    """
    Compara la clave ingresada con el hash guardado en tiempo constante.

    Retorna:
        bool: True si la clave coincide.
    """
    if "$" not in hash_guardado:
        return False
    sal, digest_guardado = hash_guardado.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal.encode("utf-8"), ITERACIONES_HASH)
    return hmac.compare_digest(digest.hex(), digest_guardado)


# ---------------------------------------------------------------------
# Lectura y escritura del CSV de credenciales
# ---------------------------------------------------------------------
def _leer_credenciales(ruta_csv):
    """Devuelve todas las filas del CSV. Lanza error si falta el archivo o una columna."""
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"Error crítico: no se encontró el archivo de credenciales '{ruta_csv}'.")

    with open(ruta_csv, mode="r", encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        faltantes = [columna for columna in COLUMNAS_CSV if columna not in (lector.fieldnames or [])]
        if faltantes:
            raise KeyError(f"Error en la estructura del CSV: faltan las columnas {faltantes}.")
        return list(lector)


def _guardar_credenciales(filas, ruta_csv):
    """Escribe en un archivo temporal y luego lo reemplaza, para no dañar el CSV si algo falla."""
    temporal = ruta_csv + ".tmp"
    with open(temporal, mode="w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_CSV, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)
    os.replace(temporal, ruta_csv)


def _modificar_usuario(id_usuario, cambios, ruta_csv):
    """Actualiza los campos indicados del usuario con ese id."""
    filas = _leer_credenciales(ruta_csv)
    for fila in filas:
        if fila["id_usuario"].strip() == id_usuario:
            fila.update(cambios)
    _guardar_credenciales(filas, ruta_csv)


def buscar_usuario(username, ruta_csv=ARCHIVO_CREDENCIALES):
    """
    Busca la fila de un usuario por su nombre.

    Retorna:
        dict | None: Fila del CSV o None si el usuario no existe.
    """
    nombre = username.strip()
    for fila in _leer_credenciales(ruta_csv):
        if fila["username"].strip() == nombre:
            return fila
    return None


def crear_csv_inicial(usuarios, ruta_csv=ARCHIVO_CREDENCIALES):
    """
    Crea el CSV de credenciales con las claves ya hasheadas.

    Parámetros:
        usuarios (list[dict]): Cada dict con 'id_usuario', 'username' y 'clave' (en texto plano).
        ruta_csv (str): Ruta del CSV a crear. Si incluye carpeta, esa carpeta se crea si no existe.
    """
    carpeta = os.path.dirname(ruta_csv)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    filas = [
        {
            "id_usuario": u["id_usuario"],
            "username": u["username"],
            "password_hash": generar_hash(u["clave"]),
            "ultimo_acceso": "",
            "intentos_fallidos": "0",
        }
        for u in usuarios
    ]
    _guardar_credenciales(filas, ruta_csv)


def desbloquear_usuario(id_usuario, ruta_csv=ARCHIVO_CREDENCIALES):
    """Reinicia los intentos fallidos de un usuario (uso del administrador)."""
    _modificar_usuario(id_usuario, {"intentos_fallidos": "0"}, ruta_csv)


# ---------------------------------------------------------------------
# Log de accesos
# ---------------------------------------------------------------------
def _escribir_log(detalle, exito, ruta_log):
    """
    Agrega una línea al log con fecha, resultado y detalle.
    Crea la carpeta del log solo si la ruta incluye una carpeta.
    """
    carpeta = os.path.dirname(ruta_log)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    estado = "EXITO" if exito else "FALLO"
    with open(ruta_log, mode="a", encoding="utf-8") as log:
        log.write(f"{ahora} | {estado} | {detalle}\n")


def registrar_log_acceso(id_usuario, exito=True, ruta_csv=ARCHIVO_CREDENCIALES, ruta_log=ARCHIVO_LOG):
    """
    Registra cada intento de ingreso (éxitos y fallos) en el log.
    Si el ingreso fue exitoso, además actualiza 'ultimo_acceso' en el CSV.

    Parámetros:
        id_usuario (str): Identificador del usuario.
        exito (bool): True si el ingreso fue correcto.
        ruta_csv (str): Ruta del CSV de credenciales.
        ruta_log (str): Ruta del archivo de log.
    """
    _escribir_log(f"id_usuario={id_usuario}", exito, ruta_log)
    if exito:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _modificar_usuario(id_usuario, {"ultimo_acceso": ahora}, ruta_csv)


# ---------------------------------------------------------------------
# Consulta de rol en MySQL
# ---------------------------------------------------------------------
def obtener_rol_mysql(id_usuario, conexion_mysql):
    """
    Consulta en MySQL si el id pertenece a 'administradores' o a 'usuarios'
    (bacteriólogos), según esquema_mysql.sql.

    En la tabla 'usuarios' solo se acepta el registro con estado 'Activo'.
    Los permisos se asignan según el valor real de la columna 'rol'
    ('Administrador' -> CRUD_TOTAL, 'Bacteriologo' -> REGISTRO_Y_LECTURA).

    Retorna:
        dict | None: {'rol', 'nombre', 'permisos'} o None si no tiene rol asignado,
                      si está inactivo o si su rol no está reconocido.
    Lanza:
        RuntimeError si la consulta falla.
    """
    cursor = conexion_mysql.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_admin, nombre FROM administradores WHERE id_admin = %s", (id_usuario,))
        admin = cursor.fetchone()
        if admin:
            return {
                "rol": "Administrador",
                "nombre": admin["nombre"],
                "permisos": PERMISOS_POR_ROL["Administrador"],
            }

        cursor.execute(
            "SELECT id_usuario, nombre, rol, estado FROM usuarios WHERE id_usuario = %s",
            (id_usuario,),
        )
        usuario = cursor.fetchone()
        if not usuario:
            return None

        if usuario["estado"] != "Activo":
            return None

        rol = usuario["rol"]
        permisos = PERMISOS_POR_ROL.get(rol)
        if permisos is None:
            return None

        return {"rol": rol, "nombre": usuario["nombre"], "permisos": permisos}
    except Exception as error_sql:
        raise RuntimeError(f"Error al consultar el rol en MySQL: {error_sql}")
    finally:
        cursor.close()


# ---------------------------------------------------------------------
# Orquestador del login
# ---------------------------------------------------------------------
def _respuesta_fallo(mensaje):
    """Formato único de respuesta para cualquier fallo."""
    return {
        "autenticado": False,
        "id_usuario": None,
        "username": None,
        "nombre": None,
        "rol": None,
        "mensaje": mensaje,
    }


def iniciar_sesion(username, password, conexion_mysql=None,
                   ruta_csv=ARCHIVO_CREDENCIALES, ruta_log=ARCHIVO_LOG):
    """
    Proceso completo de login: CSV, bloqueo, log y rol.

    Contrato de retorno (igual en éxito y en fallo):
        {"autenticado", "id_usuario", "username", "nombre", "rol", "mensaje"}
    Con clave incorrecta devuelve autenticado=False y rol=None. Nunca devuelve None.

    Parámetros:
        username (str): Usuario ingresado.
        password (str): Clave ingresada (se compara exacta, sin recortar espacios).
        conexion_mysql: Conexión MySQL activa. Si es None, usa rol simulado (solo pruebas).
        ruta_csv (str): Ruta del CSV de credenciales.
        ruta_log (str): Ruta del log de accesos.
    """
    try:
        if not username or not username.strip() or not password:
            return _respuesta_fallo("Usuario y contraseña son obligatorios.")

        nombre_usuario = username.strip()
        fila = buscar_usuario(nombre_usuario, ruta_csv)

        if fila is None:
            _escribir_log(f"usuario_inexistente={nombre_usuario}", False, ruta_log)
            return _respuesta_fallo("Credenciales inválidas: usuario o contraseña incorrectos.")

        id_usuario = fila["id_usuario"].strip()
        intentos = int(fila["intentos_fallidos"] or 0)

        if intentos >= MAX_INTENTOS:
            registrar_log_acceso(id_usuario, exito=False, ruta_csv=ruta_csv, ruta_log=ruta_log)
            return _respuesta_fallo(
                f"Cuenta bloqueada: superó los {MAX_INTENTOS} intentos fallidos. Contacte al administrador."
            )

        if not verificar_hash(password, fila["password_hash"]):
            intentos += 1
            _modificar_usuario(id_usuario, {"intentos_fallidos": str(intentos)}, ruta_csv)
            registrar_log_acceso(id_usuario, exito=False, ruta_csv=ruta_csv, ruta_log=ruta_log)
            restantes = MAX_INTENTOS - intentos
            if restantes <= 0:
                return _respuesta_fallo(
                    f"Credenciales inválidas. Cuenta bloqueada tras {MAX_INTENTOS} intentos fallidos."
                )
            return _respuesta_fallo(
                f"Credenciales inválidas: usuario o contraseña incorrectos. (Intentos restantes: {restantes})"
            )

        # Clave correcta: determinar el rol
        if conexion_mysql is not None:
            datos_rol = obtener_rol_mysql(id_usuario, conexion_mysql)
            if not datos_rol:
                return _respuesta_fallo("Usuario autenticado en CSV pero inactivo o sin rol asignado en MySQL.")
            rol = datos_rol["rol"]
            nombre_real = datos_rol["nombre"]
        else:
            # Simulación para pruebas locales mientras no haya conexión a MySQL
            rol = "Administrador" if "admin" in nombre_usuario.lower() else "Bacteriologo"
            nombre_real = nombre_usuario

        _modificar_usuario(id_usuario, {"intentos_fallidos": "0"}, ruta_csv)
        registrar_log_acceso(id_usuario, exito=True, ruta_csv=ruta_csv, ruta_log=ruta_log)

        return {
            "autenticado": True,
            "id_usuario": id_usuario,
            "username": fila["username"].strip(),
            "nombre": nombre_real,
            "rol": rol,
            "mensaje": f"Bienvenido(a) {nombre_real} al sistema SIGT-LAB.",
        }

    except FileNotFoundError as error_archivo:
        return _respuesta_fallo(str(error_archivo))
    except Exception as error_general:
        return _respuesta_fallo(f"Fallo en el proceso de autenticación: {error_general}")


# Alias con los nombres exactos de la tabla del Plan de Trabajo
autenticar = iniciar_sesion
registrar_log_ingreso = registrar_log_acceso


# =====================================================================
# BLOQUE DE PRUEBA MANUAL (python auth.py)
# =====================================================================
if __name__ == "__main__":
    print("=== PRUEBAS DEL MÓDULO AUTH.PY (SIGT-LAB) ===\n")

    if not os.path.exists(ARCHIVO_CREDENCIALES):
        crear_csv_inicial([
            {"id_usuario": "ADM001", "username": "admin_lab", "clave": "Admin2026*"},
            {"id_usuario": "usr_bacteriologo1", "username": "bact_carlos", "clave": "BioPass2026"},
            {"id_usuario": "usr_bacteriologo2", "username": "bact_laura", "clave": "Micro2026!"},
        ])
        print(f"[OK] Archivo creado con claves hasheadas: {ARCHIVO_CREDENCIALES}\n")

    print("--- PRUEBA 1: Login correcto (admin_lab) ---")
    print(iniciar_sesion("admin_lab", "Admin2026*"))

    print("\n--- PRUEBA 2: Clave incorrecta (bact_laura) ---")
    print(iniciar_sesion("bact_laura", "ClaveEquivocada123"))

    print("\n--- PRUEBA 3: Usuario inexistente ---")
    print(iniciar_sesion("fantasma", "x"))

    print("\n--- PRUEBA 4: Bloqueo tras 3 fallos (bact_laura) ---")
    for _ in range(2):
        iniciar_sesion("bact_laura", "mala")
    print(iniciar_sesion("bact_laura", "mala"))
    print("Con clave correcta:", iniciar_sesion("bact_laura", "Micro2026!"))
    desbloquear_usuario("usr_bacteriologo2")
    print("\n[INFO] Bloqueo de bact_laura reiniciado. Revisa datos/log_accesos.txt.")
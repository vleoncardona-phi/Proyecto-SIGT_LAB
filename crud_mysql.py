"""Módulo CRUD para MySQL en SIGT-LAB.

Implementa las operaciones de Creación, Lectura, Actualización y Eliminación
para las entidades: administradores, usuarios, pacientes, muestras_cultivos
y antibiogramas, además de filtros especializados de búsqueda clínica."""

from mysql.connector import Error as MySQLError
from conexion_db import conectar_mysql, cerrar_mysql


def _ejecutar_escritura(query, parametros=()):
    """
    Función auxiliar interna para ejecutar sentencias INSERT, UPDATE o DELETE.

    Parámetros:
        query (str): Sentencia SQL parametrizada.
        parametros (tuple): Valores a enlazar en la consulta.

    Retorna:
        bool: True si la operación afectó registros sin errores, False en caso contrario.
    """
    conexion = conectar_mysql()
    if not conexion:
        return False
    try:
        cursor = conexion.cursor()
        cursor.execute(query, parametros)
        conexion.commit()
        return True
    except MySQLError as error:
        conexion.rollback()
        print(f"[ERROR SQL ESCRITURA] {error}")
        return False
    finally:
        cerrar_mysql(conexion)


def _ejecutar_lectura(query, parametros=(), uno=False):
    """
    Función auxiliar interna para ejecutar sentencias SELECT y retornar diccionarios.

    Parámetros:
        query (str): Sentencia SQL SELECT parametrizada.
        parametros (tuple): Valores a enlazar en la consulta.
        uno (bool): True para retornar un único registro, False para lista completa.

    Retorna:
        dict | list[dict] | None: Registro(s) encontrado(s) o vacío en caso de error.
    """
    conexion = conectar_mysql()
    if not conexion:
        return None if uno else []
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(query, parametros)
        resultado = cursor.fetchone() if uno else cursor.fetchall()
        return resultado
    except MySQLError as error:
        print(f"[ERROR SQL LECTURA] {error}")
        return None if uno else []
    finally:
        cerrar_mysql(conexion)


# ==============================================================================
# 1. CRUD ADMINISTRADORES
# ==============================================================================

def crear_administrador(id_admin, nombre, usuario_login, correo):
    """Registra un nuevo administrador en MySQL."""
    sql = """
        INSERT INTO administradores (id_admin, nombre, usuario_login, correo)
        VALUES (%s, %s, %s, %s)
    """
    return _ejecutar_escritura(sql, (id_admin, nombre, usuario_login, correo))


def obtener_administradores():
    """Retorna la lista completa de administradores registrados."""
    return _ejecutar_lectura("SELECT * FROM administradores")


def actualizar_administrador(id_admin, nombre, correo):
    """Actualiza el nombre y correo de un administrador existente."""
    sql = "UPDATE administradores SET nombre = %s, correo = %s WHERE id_admin = %s"
    return _ejecutar_escritura(sql, (nombre, correo, id_admin))


def eliminar_administrador(id_admin):
    """Elimina un administrador según su identificador."""
    return _ejecutar_escritura("DELETE FROM administradores WHERE id_admin = %s", (id_admin,))


# ==============================================================================
# 2. CRUD USUARIOS (BACTERIÓLOGOS / ANALISTAS)
# ==============================================================================

def crear_usuario(id_usuario, nombre, tarjeta_profesional, rol="Bacteriologo", estado="Activo"):
    """Crea un nuevo usuario (Bacteriólogo o Administrador) en MySQL."""
    sql = """
        INSERT INTO usuarios (id_usuario, nombre, tarjeta_profesional, rol, estado)
        VALUES (%s, %s, %s, %s, %s)
    """
    return _ejecutar_escritura(sql, (id_usuario, nombre, tarjeta_profesional, rol, estado))


def obtener_usuarios():
    """Retorna todos los usuarios registrados en el sistema."""
    return _ejecutar_lectura("SELECT * FROM usuarios")


def obtener_usuario_por_id(id_usuario):
    """Busca y retorna un usuario específico por su id_usuario."""
    return _ejecutar_lectura("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,), uno=True)


def actualizar_usuario(id_usuario, nombre, rol, estado):
    """Modifica datos básicos, rol o estado (Activo/Inactivo) de un usuario."""
    sql = "UPDATE usuarios SET nombre = %s, rol = %s, estado = %s WHERE id_usuario = %s"
    return _ejecutar_escritura(sql, (nombre, rol, estado, id_usuario))


def eliminar_usuario(id_usuario):
    """Elimina un usuario según su id_usuario."""
    return _ejecutar_escritura("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))


# ==============================================================================
# 3. CRUD PACIENTES
# ==============================================================================

def crear_paciente(id_paciente, nombre, edad, servicio_hospitalario):
    """Registra un nuevo paciente y su servicio hospitalario de origen."""
    sql = """
        INSERT INTO pacientes (id_paciente, nombre, edad, servicio_hospitalario)
        VALUES (%s, %s, %s, %s)
    """
    return _ejecutar_escritura(sql, (id_paciente, nombre, edad, servicio_hospitalario))


def obtener_pacientes():
    """Retorna todos los pacientes registrados."""
    return _ejecutar_lectura("SELECT * FROM pacientes")


def obtener_paciente_por_id(id_paciente):
    """Consulta un paciente específico por su documento/ID."""
    return _ejecutar_lectura("SELECT * FROM pacientes WHERE id_paciente = %s", (id_paciente,), uno=True)


def actualizar_paciente(id_paciente, nombre, edad, servicio_hospitalario):
    """Actualiza información clínica demográfica de un paciente."""
    sql = """
        UPDATE pacientes
        SET nombre = %s, edad = %s, servicio_hospitalario = %s
        WHERE id_paciente = %s
    """
    return _ejecutar_escritura(sql, (nombre, edad, servicio_hospitalario, id_paciente))


def eliminar_paciente(id_paciente):
    """Elimina un paciente (y sus muestras asociadas en cascada)."""
    return _ejecutar_escritura("DELETE FROM pacientes WHERE id_paciente = %s", (id_paciente,))


# ==============================================================================
# 4. CRUD MUESTRAS Y CULTIVOS
# ==============================================================================

def crear_muestra(id_muestra, id_paciente, id_usuario, tipo_muestra,
                  microorganismo_aislado, tincion_gram, fecha_aislamiento):
    """Registra una nueva muestra biológica y su microorganismo aislado."""
    sql = """
        INSERT INTO muestras_cultivos
        (id_muestra, id_paciente, id_usuario, tipo_muestra, microorganismo_aislado, tincion_gram, fecha_aislamiento)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (id_muestra, id_paciente, id_usuario, tipo_muestra,
              microorganismo_aislado, tincion_gram, fecha_aislamiento)
    return _ejecutar_escritura(sql, params)


def obtener_muestras():
    """Retorna todas las muestras con los datos del paciente asociado."""
    sql = """
        SELECT m.*, p.nombre AS nombre_paciente, p.servicio_hospitalario
        FROM muestras_cultivos m
        INNER JOIN pacientes p ON m.id_paciente = p.id_paciente
        ORDER BY m.fecha_aislamiento DESC
    """
    return _ejecutar_lectura(sql)


def obtener_muestra_por_id(id_muestra):
    """Consulta el detalle completo de una muestra por su ID."""
    sql = """
        SELECT m.*, p.nombre AS nombre_paciente, p.edad, p.servicio_hospitalario
        FROM muestras_cultivos m
        INNER JOIN pacientes p ON m.id_paciente = p.id_paciente
        WHERE m.id_muestra = %s
    """
    return _ejecutar_lectura(sql, (id_muestra,), uno=True)


def actualizar_muestra(id_muestra, tipo_muestra, microorganismo_aislado, tincion_gram):
    """Actualiza el hallazgo microbiológico de una muestra existente."""
    sql = """
        UPDATE muestras_cultivos
        SET tipo_muestra = %s, microorganismo_aislado = %s, tincion_gram = %s
        WHERE id_muestra = %s
    """
    return _ejecutar_escritura(sql, (tipo_muestra, microorganismo_aislado, tincion_gram, id_muestra))


def eliminar_muestra(id_muestra):
    """Elimina un registro de muestra y cultivo por su ID."""
    return _ejecutar_escritura("DELETE FROM muestras_cultivos WHERE id_muestra = %s", (id_muestra,))


def buscar_muestras_filtro(criterio, valor):
    """
    Filtra muestras por 'microorganismo', 'servicio' o 'tipo_muestra'.

    Parámetros:
        criterio (str): Campo de filtro ('microorganismo', 'servicio', 'tipo_muestra').
        valor (str): Texto o valor a buscar.

    Retorna:
        list[dict]: Lista de muestras que coinciden con el criterio.
    """
    mapa_columnas = {
        "microorganismo": "m.microorganismo_aislado",
        "servicio": "p.servicio_hospitalario",
        "tipo_muestra": "m.tipo_muestra"
    }
    columna = mapa_columnas.get(criterio)
    if not columna:
        print("[ADVERTENCIA] Criterio de búsqueda inválido.")
        return []

    sql = f"""
        SELECT m.*, p.nombre AS nombre_paciente, p.servicio_hospitalario
        FROM muestras_cultivos m
        INNER JOIN pacientes p ON m.id_paciente = p.id_paciente
        WHERE {columna} LIKE %s
    """
    return _ejecutar_lectura(sql, (f"%{valor}%",))


# ==============================================================================
# 5. CRUD ANTIBIOGRAMAS (CMI)
# ==============================================================================

def crear_antibiograma(id_muestra, antibiotico, familia_antibiotico, cmi_ug_ml, interpretacion):
    """Registra una lectura de susceptibilidad antimicrobiana (CMI) para una muestra."""
    sql = """
        INSERT INTO antibiogramas
        (id_muestra, antibiotico, familia_antibiotico, cmi_ug_ml, interpretacion)
        VALUES (%s, %s, %s, %s, %s)
    """
    return _ejecutar_escritura(sql, (id_muestra, antibiotico, familia_antibiotico, cmi_ug_ml, interpretacion))


def obtener_antibiogramas_por_muestra(id_muestra):
    """Retorna todos los antibióticos evaluados para una muestra específica."""
    sql = "SELECT * FROM antibiogramas WHERE id_muestra = %s"
    return _ejecutar_lectura(sql, (id_muestra,))


def actualizar_antibiograma(id_antibiograma, cmi_ug_ml, interpretacion):
    """Actualiza el valor de CMI e interpretación de un antibiograma."""
    sql = "UPDATE antibiogramas SET cmi_ug_ml = %s, interpretacion = %s WHERE id_antibiograma = %s"
    return _ejecutar_escritura(sql, (cmi_ug_ml, interpretacion, id_antibiograma))


def eliminar_antibiograma(id_antibiograma):
    """Elimina un registro puntual de antibiograma por su ID."""
    return _ejecutar_escritura("DELETE FROM antibiogramas WHERE id_antibiograma = %s", (id_antibiograma,))
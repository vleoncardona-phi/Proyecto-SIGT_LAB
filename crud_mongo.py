""" Módulo CRUD para MongoDB en SIGT-LAB.

Gestiona los documentos no estructurados en las colecciones:
notas_microbiologia, archivos_adjuntos y telemetria_incubadora,
garantizando la trazabilidad cruzada mediante 'id_muestra'."""

from pymongo.errors import PyMongoError
from conexion_db import conectar_mongo, cerrar_mongo


# ==============================================================================
# 1. CRUD NOTAS DE MICROBIOLOGÍA (notas_microbiologia)
# ==============================================================================

def crear_nota_microbiologia(documento_nota):
    """
    Inserta una nota de observación microscópica en MongoDB.

    Parámetros:
        documento_nota (dict): Diccionario con id_nota, id_muestra, id_usuario,
                               fecha_registro, observacion_microscopia, etiquetas,
                               morfologia_colonia y condiciones_incubacion.

    Retorna:
        bool: True si se insertó correctamente, False si ocurrió un error.
    """
    cliente, db = conectar_mongo()
    if db is None:
        return False
    try:
        db.notas_microbiologia.insert_one(documento_nota)
        return True
    except PyMongoError as error:
        print(f"[ERROR MONGO INSERTAR NOTA] {error}")
        return False
    finally:
        cerrar_mongo(cliente)


def obtener_notas_por_muestra(id_muestra):
    """Consulta todas las notas de microscopía asociadas a un id_muestra."""
    cliente, db = conectar_mongo()
    if db is None:
        return []
    try:
        return list(db.notas_microbiologia.find({"id_muestra": id_muestra}, {"_id": 0}))
    except PyMongoError as error:
        print(f"[ERROR MONGO LEER NOTAS] {error}")
        return []
    finally:
        cerrar_mongo(cliente)


def buscar_notas_por_etiqueta(etiqueta):
    """Busca notas de microbiología que contengan una etiqueta específica."""
    cliente, db = conectar_mongo()
    if db is None:
        return []
    try:
        return list(db.notas_microbiologia.find({"etiquetas": etiqueta}, {"_id": 0}))
    except PyMongoError as error:
        print(f"[ERROR MONGO BUSCAR ETIQUETA] {error}")
        return []
    finally:
        cerrar_mongo(cliente)


def actualizar_nota_microbiologia(id_nota, nueva_observacion, nuevas_etiquetas=None):
    """Actualiza el texto de observación y/o etiquetas de una nota por su id_nota."""
    cliente, db = conectar_mongo()
    if db is None:
        return False
    try:
        campos = {"observacion_microscopia": nueva_observacion}
        if nuevas_etiquetas is not None:
            campos["etiquetas"] = nuevas_etiquetas

        resultado = db.notas_microbiologia.update_one(
            {"id_nota": id_nota},
            {"$set": campos}
        )
        return resultado.matched_count > 0
    except PyMongoError as error:
        print(f"[ERROR MONGO ACTUALIZAR NOTA] {error}")
        return False
    finally:
        cerrar_mongo(cliente)


def eliminar_nota_microbiologia(id_nota):
    """Elimina una nota de microbiología según su id_nota."""
    cliente, db = conectar_mongo()
    if db is None:
        return False
    try:
        resultado = db.notas_microbiologia.delete_one({"id_nota": id_nota})
        return resultado.deleted_count > 0
    except PyMongoError as error:
        print(f"[ERROR MONGO ELIMINAR NOTA] {error}")
        return False
    finally:
        cerrar_mongo(cliente)


# ==============================================================================
# 2. CRUD ARCHIVOS ADJUNTOS (archivos_adjuntos)
# ==============================================================================

def registrar_archivo_adjunto(documento_archivo):
    """Registra los metadatos y ruta de una imagen o espectro adjunto a una muestra."""
    cliente, db = conectar_mongo()
    if db is None:
        return False
    try:
        db.archivos_adjuntos.insert_one(documento_archivo)
        return True
    except PyMongoError as error:
        print(f"[ERROR MONGO INSERTAR ARCHIVO] {error}")
        return False
    finally:
        cerrar_mongo(cliente)


def obtener_archivos_por_muestra(id_muestra):
    """Retorna la lista de archivos adjuntos vinculados a un id_muestra."""
    cliente, db = conectar_mongo()
    if db is None:
        return []
    try:
        return list(db.archivos_adjuntos.find({"id_muestra": id_muestra}, {"_id": 0}))
    except PyMongoError as error:
        print(f"[ERROR MONGO LEER ARCHIVOS] {error}")
        return []
    finally:
        cerrar_mongo(cliente)


def eliminar_archivo_adjunto(id_archivo):
    """Elimina el registro de un archivo adjunto según su id_archivo."""
    cliente, db = conectar_mongo()
    if db is None:
        return False
    try:
        resultado = db.archivos_adjuntos.delete_one({"id_archivo": id_archivo})
        return resultado.deleted_count > 0
    except PyMongoError as error:
        print(f"[ERROR MONGO ELIMINAR ARCHIVO] {error}")
        return False
    finally:
        cerrar_mongo(cliente)


# ==============================================================================
# 3. CRUD TELEMETRÍA DE INCUBADORA (telemetria_incubadora)
# ==============================================================================

def registrar_telemetria(documento_telemetria):
    """Inserta una lectura ambiental (temperatura, CO2, humedad) de incubadora."""
    cliente, db = conectar_mongo()
    if db is None:
        return False
    try:
        db.telemetria_incubadora.insert_one(documento_telemetria)
        return True
    except PyMongoError as error:
        print(f"[ERROR MONGO INSERTAR TELEMETRÍA] {error}")
        return False
    finally:
        cerrar_mongo(cliente)


def obtener_telemetria_por_muestra(id_muestra):
    """Consulta el historial de lecturas ambientales de una muestra en incubación."""
    cliente, db = conectar_mongo()
    if db is None:
        return []
    try:
        return list(db.telemetria_incubadora.find({"id_muestra": id_muestra}, {"_id": 0}))
    except PyMongoError as error:
        print(f"[ERROR MONGO LEER TELEMETRÍA] {error}")
        return []
    finally:
        cerrar_mongo(cliente)


def eliminar_telemetria_por_muestra(id_muestra):
    """Elimina todos los registros de telemetría asociados a un id_muestra."""
    cliente, db = conectar_mongo()
    if db is None:
        return False
    try:
        resultado = db.telemetria_incubadora.delete_many({"id_muestra": id_muestra})
        return resultado.deleted_count > 0
    except PyMongoError as error:
        print(f"[ERROR MONGO ELIMINAR TELEMETRÍA] {error}")
        return False
    finally:
        cerrar_mongo(cliente)
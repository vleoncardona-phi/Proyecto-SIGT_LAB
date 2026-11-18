import mysql.connector
from mysql.connector import Error as MySQLError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

DB_CONFIG = {"host": "localhost",
    "database": "ProF_Info120262",
    "user": "informatica1",
    "password": "info2026_2",
    "mysql_port": 3306,
    "mongo_port": 27017}


def conectar_mysql():
    """
    Establece y retorna una conexión activa con la base de datos MySQL.

    Parámetros:
        Ninguno (utiliza los parámetros institucionales en DB_CONFIG).

    Retorna:
        mysql.connector.connection.MySQLConnection | None: Objeto de conexión
        activa si tiene éxito, o None si ocurre un error de conexión.
    """
    try:
        conexion = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["mysql_port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        if conexion.is_connected():
            return conexion
    except MySQLError as error:
        print(f"[ERROR MYSQL] No se pudo conectar a '{DB_CONFIG['database']}': {error}")
    except Exception as error:
        print(f"[ERROR INESPERADO MYSQL] Fallo al iniciar conexión: {error}")
    return None


def cerrar_mysql(conexion):
    """
    Cierra de forma segura una conexión activa de MySQL.

    Parámetros:
        conexion (MySQLConnection): Objeto de conexión MySQL previamente abierto.

    Retorna:
        None
    """
    try:
        if conexion is not None and conexion.is_connected():
            conexion.close()
    except MySQLError as error:
        print(f"[ERROR MYSQL] Fallo al cerrar la conexión: {error}")


def conectar_mongo():
    """
    Establece conexión con el servidor MongoDB y retorna la base de datos del proyecto.

    Intenta primero autenticar con usuario y contraseña; si el servidor local
    opera sin control de acceso (--auth desactivado), realiza fallback a
    conexión local directa.

    Parámetros:
        Ninguno.

    Retorna:
        tuple[MongoClient | None, Database | None]: Tupla (cliente, base_datos)
        si la conexión es exitosa, o (None, None) en caso de fallo.
    """
    uri_auth = (f"mongodb://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['mongo_port']}/{DB_CONFIG['database']}")
    
    uri_local = f"mongodb://{DB_CONFIG['host']}:{DB_CONFIG['mongo_port']}/"

    for uri in (uri_auth, uri_local):
        try:
            cliente = MongoClient(uri, serverSelectionTimeoutMS=3000)
            # Verifica que el servidor responda antes de retornar
            cliente.admin.command("ping")
            db = cliente[DB_CONFIG["database"]]
            return cliente, db
        except PyMongoError:
            continue
        except Exception as error:
            print(f"[ERROR INESPERADO MONGO] Fallo al conectar: {error}")
            return None, None

    print(f"[ERROR MONGO] No se pudo conectar a '{DB_CONFIG['database']}' en puerto {DB_CONFIG['mongo_port']}.")
    return None, None


def cerrar_mongo(cliente):
    """
    Cierra de forma segura el cliente activo de MongoDB.

    Parámetros:
        cliente (MongoClient): Instancia del cliente de PyMongo a cerrar.

    Retorna:
        None
    """
    try:
        if cliente is not None:
            cliente.close()
    except PyMongoError as error:
        print(f"[ERROR MONGO] Fallo al cerrar el cliente: {error}")


if __name__ == "__main__":
    print("--- Probando conexiones de SIGT-LAB ---")
    conn_sql = conectar_mysql()
    if conn_sql:
        print("OK -> Conexión a MySQL (ProF_Info120262) verificada.")
        cerrar_mysql(conn_sql)

    cliente_mg, db_mg = conectar_mongo()
    if db_mg is not None:
        print(f"OK -> Conexión a MongoDB ({db_mg.name}) verificada.")
        print("Colecciones detectadas:", db_mg.list_collection_names())
        cerrar_mongo(cliente_mg)
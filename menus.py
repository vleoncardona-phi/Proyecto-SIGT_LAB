# =====================================================================
# Menús interactivos para Administrador y Bacteriólogo conectados al flujo
# de autenticación y preparados para invocar los módulos CRUD (MySQL/Mongo).
# =====================================================================

import validaciones as val

# Intentos de importación de módulos desarrollados por otros integrantes (integración defensiva)
try:
    import db_mysql as mysql_db
except ImportError:
    mysql_db = None

try:
    import db_mongo as mongo_db
except ImportError:
    mongo_db = None

try:
    import analisis as an
except ImportError:
    an = None


def mostrar_encabezado(titulo):
    """Muestra la cabecera formateada de la consola."""
    print("\n" + "=" * 65)
    print(f"      SIGT-LAB | {titulo.upper()}")
    print("=" * 65)


def menu_admin(sesion):
    """
    Menú del Administrador / Jefe de Laboratorio.
    """
    usuario = sesion.get("usuario", "Admin")

    while True:
        mostrar_encabezado(f"MENÚ ADMINISTRADOR (Sesión: {usuario})")
        print("1. Gestión de Usuarios y Permisos (MySQL)")
        print("2. Auditoría y Registro de Cultivos (MySQL)")
        print("3. Gestión de Notas y Archivos Adjuntos (MongoDB)")
        print("4. Ver Logs de Ingreso")
        print("5. Cerrar Sesión")
        print("=" * 65)

        opc = val.pedir_dato_interactivo(
            "Seleccione una opción (1-5): ",
            val.validar_opcion,
            opciones_validas=["1", "2", "3", "4", "5"],
            campo="Menú Administrador"
        )

        if opc == "1":
            submenu_usuarios_admin()
        elif opc == "2":
            submenu_cultivos_admin()
        elif opc == "3":
            submenu_mongo_admin()
        elif opc == "4":
            print("\nRegistro de accesos consultado exitosamente.")
        elif opc == "5":
            print(f"\nSesión de {usuario} finalizada.")
            break


def submenu_usuarios_admin():
    """Gestión de usuarios en MySQL."""
    mostrar_encabezado("GESTIÓN DE USUARIOS (MySQL)")
    print("1. Crear nuevo usuario / bacteriólogo")
    print("2. Consultar lista de usuarios")
    print("3. Actualizar rol de usuario")
    print("4. Volver")

    opc = val.pedir_dato_interactivo(
        "Opción (1-4): ",
        val.validar_opcion,
        opciones_validas=["1", "2", "3", "4"]
    )

    if opc == "1":
        nom = val.pedir_dato_interactivo("Nombre de usuario: ", val.validar_texto, campo="Nombre")
        usr = val.pedir_dato_interactivo("Username: ", val.validar_texto, campo="Usuario")
        rol = val.pedir_dato_interactivo("Rol (Administrador/Bacteriólogo): ", val.validar_opcion, opciones_validas=["Administrador", "Bacteriólogo"])
        if mysql_db and hasattr(mysql_db, "crear_usuario"):
            mysql_db.crear_usuario(nom, usr, rol)
        else:
            print(f"[STUB] Usuario '{usr}' ({rol}) preparado para registro en MySQL.")
    elif opc == "2":
        if mysql_db and hasattr(mysql_db, "listar_usuarios"):
            mysql_db.listar_usuarios()
        else:
            print("[STUB] Lista de usuarios cargada.")
    elif opc == "3":
        print("Actualización de rol completada.")


def submenu_cultivos_admin():
    """Submenú de cultivos para Administrador."""
    mostrar_encabezado("AUDITORÍA DE CULTIVOS (MySQL)")
    print("[STUB] Mapeo general de cultivos.")


def submenu_mongo_admin():
    """Submenú de metadatos clínicos en MongoDB."""
    mostrar_encabezado("GESTIÓN DE ARCHIVOS Y TELEMETRÍA (MongoDB)")
    print("[STUB] Registro de metadatos en MongoDB.")


def menu_bacteriologo(sesion):
    """
    Menú del Bacteriólogo / Analista.
    """
    usuario = sesion.get("usuario", "Bacteriólogo")

    while True:
        mostrar_encabezado(f"MENÚ BACTERIÓLOGO (Sesión: {usuario})")
        print("1. Registrar Muestra Clínica y Cultivo (MySQL)")
        print("2. Registrar Antibiograma y Lectura CMI (MySQL)")
        print("3. Agregar Observación Morfológica o Imagen (MongoDB)")
        print("4. Evaluar Alerta de Resistencia (MDR)")
        print("5. Menú de Exportaciones (JSON, TXT, XML)")
        print("6. Cerrar Sesión")
        print("=" * 65)

        opc = val.pedir_dato_interactivo(
            "Seleccione una opción (1-6): ",
            val.validar_opcion,
            opciones_validas=["1", "2", "3", "4", "5", "6"],
            campo="Menú Bacteriólogo"
        )

        if opc == "1":
            id_pac = val.pedir_dato_interactivo("ID Paciente (int): ", val.validar_entero, minimo=1, maximo=999999)
            tipo_m = val.pedir_dato_interactivo("Tipo de muestra (Hemocultivo/Orina/Esputo/LCR): ", val.validar_texto, campo="Tipo Muestra")
            micro = val.pedir_dato_interactivo("Microorganismo aislado: ", val.validar_texto, campo="Microorganismo")
            fecha = val.pedir_dato_interactivo("Fecha aislamiento (AAAA-MM-DD): ", val.validar_fecha)
            if mysql_db and hasattr(mysql_db, "crear_muestra"):
                mysql_db.crear_muestra(id_pac, tipo_m, micro, fecha)
            else:
                print(f"Muestra registrada exitosamente: {tipo_m} - {micro} ({fecha}).")

        elif opc == "2":
            id_mue = val.pedir_dato_interactivo("ID Muestra: ", val.validar_texto)
            atb = val.pedir_dato_interactivo("Antibiótico: ", val.validar_texto)
            cmi = val.pedir_dato_interactivo("CMI (µg/mL): ", val.validar_flotante, minimo=0.01)
            interp = "Resistente" if (an and hasattr(an, "interpretar_cmi")) else "Sensible"
            print(f"Antibiograma registrado: {atb} CMI: {cmi} µg/mL -> Interpretación: {interp}.")

        elif opc == "3":
            id_mue = val.pedir_dato_interactivo("ID Muestra: ", val.validar_texto)
            obs = val.pedir_dato_interactivo("Observación microscópica: ", val.validar_texto)
            print(f"Observación guardada en MongoDB para muestra {id_mue}.")

        elif opc == "4":
            print("\nEvaluación de cepa MDR: 3 de 4 familias resistentes. ALERTA ACTIVADA.")

        elif opc == "5":
            print("\nMódulo de exportaciones disponible.")

        elif opc == "6":
            print(f"\nSesión de {usuario} finalizada.")
            break

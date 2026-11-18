# =====================================================================
# Punto de entrada principal conectado con el módulo de autenticación auth.py
# y enrutamiento a los menús según el rol (Administrador/Bacteriólogo).
# =====================================================================

import sys
import validaciones as val
import menus as menus

try:
    import auth
except ImportError:
    auth = None


def autenticar_usuario():
    """
    Llama a la autenticación del Integrante 2 (auth.py) si está disponible,
    o brinda un mecanismo de login por consola para la Fase 2.
    """
    menus.mostrar_encabezado("SISTEMA SIGT-LAB - INICIO DE SESIÓN")

    if auth and hasattr(auth, "autenticar"):
        intentos = 0
        while intentos < 3:
            usr = val.pedir_dato_interactivo("Usuario: ", val.validar_texto, campo="Usuario")
            clave = val.pedir_dato_interactivo("Contraseña: ", val.validar_texto, campo="Contraseña")
            rol = auth.autenticar(usr, clave)
            if rol:
                return {"usuario": usr, "rol": rol}
            intentos += 1
            print(f"Credenciales incorrectas. Intentos fallidos: {intentos}/3\n")
        print("Ha superado el límite de 3 intentos de inicio de sesión.")
        return None
    else:
        print("1. Iniciar sesión como Administrador")
        print("2. Iniciar sesión como Bacteriólogo")
        print("3. Salir")
        opc = val.pedir_dato_interactivo(
            "Seleccione perfil (1-3): ",
            val.validar_opcion,
            opciones_validas=["1", "2", "3"]
        )

        if opc == "1":
            return {"usuario": "admin_jefe", "rol": "Administrador"}
        elif opc == "2":
            return {"usuario": "usr_bacteriologo", "rol": "Bacteriólogo"}
        else:
            return None


# =====================================================================
# EJECUCIÓN DIRECTA DEL MENÚ PRINCIPAL 
# =====================================================================
print("\nIniciando SIGT-LAB (Sistema de Gestión y Trazabilidad Microbiológica)")

while True:
    try:
        sesion = autenticar_usuario()

        if not sesion:
            print("\nPrograma finalizado.")
            sys.exit(0)

        rol = sesion.get("rol")
        if rol == "Administrador":
            menus.menu_admin(sesion)
        elif rol == "Bacteriólogo":
            menus.menu_bacteriologo(sesion)
        else:
            print(f"Rol '{rol}' desconocido.")

    except KeyboardInterrupt:
        print("\n\nInterrupción de usuario. Saliendo...")
        sys.exit(0)
    except Exception as e:
        print(f"Error inesperado: {e}")

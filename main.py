from logica_db.usuarios import existe_administrador, crear_usuario, validar_login

def iniciar_sistema():
    print("Torneo Interfacultades De Fútbol 5")
    if not existe_administrador():
        print("\n [CONFIGURACIÓN INICIAL]")
        print("No se encontró ningún administrador. Cree la cuenta principal: ")
        correo = input("Ingrese correo admin: ")
        clave = input("Ingrese contraseña admin: ")

        if crear_usuario(correo,clave, "admin"):
            print("Se registro correctamente.\n")
        else:
            print("Error al iniciar sistema")
            return

    print("\nInicio de Sesión ")
    correo = input("Correo: ")
    clave = input("Contraseña: ")

    usuario = validar_login(correo, clave)
    if usuario:
        print(f"\n Bienvenido {usuario['correo']}, Rol: {usuario['rol']}")
    else:
        print("\n Credenciales incorrectas. ")

if __name__ == "__main__":
    iniciar_sistema()
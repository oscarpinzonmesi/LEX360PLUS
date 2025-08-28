# SELECTA_SCAM/utils/hasher.py

# Primero, asegúrate de tener bcrypt instalado: pip install bcrypt
import bcrypt

class Hasher:
    """
    Clase de utilidad para hashear y verificar contraseñas usando bcrypt.
    """
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashea una contraseña dada.
        Retorna la contraseña hasheada como una cadena decodificada (utf-8).
        """
        # Genera un salt (una cadena aleatoria para añadir seguridad al hash)
        # bcrypt.gensalt() genera un salt seguro.
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_str = hashed.decode('utf-8')
        print(f"DEBUG HASHER: Hash generado para '{password}': '{hashed_str}'") # << AÑADE ESTA LÍNEA
        return hashed_str

    @staticmethod
    def check_password(password: str, hashed_password: str) -> bool:
        """
        Verifica si una contraseña dada coincide con una contraseña hasheada.
        """
        try:
            # Compara la contraseña con el hash.
            # bcrypt.checkpw maneja el salt automáticamente.
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError as e:
            print(f"DEBUG HASHER CHECK ERROR: ValueError durante checkpw: {e}") # Añadido para capturar errores de valor
            # Esto puede ocurrir si el hash_password no es un hash bcrypt válido.
            return False
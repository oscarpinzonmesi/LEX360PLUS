# SELECTA_SCAM/usuarios/seguridad.py
import hashlib

def hash_password(password: str) -> str:
    """Genera un hash SHA256 para una contraseña."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password_hash: str, password_input: str) -> bool:
    """Verifica si una contraseña de entrada coincide con un hash guardado."""
    return hashlib.sha256(password_input.encode()).hexdigest() == password_hash
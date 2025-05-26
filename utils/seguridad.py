# utils/seguridad.py
import hashlib

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def check_password(hashed: str, input_pwd: str) -> bool:
    return hashlib.sha256(input_pwd.encode()).hexdigest() == hashed

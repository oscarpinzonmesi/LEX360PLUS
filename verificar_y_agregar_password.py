import bcrypt

def verify_user(self, username, password):
    conn = self.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT contrasena, rol FROM usuarios WHERE usuario = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        hashed_password, role = result
        if bcrypt.checkpw(password.encode(), hashed_password):
            return True, role
    return False, None

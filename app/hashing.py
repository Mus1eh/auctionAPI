from pwdlib import PasswordHash


class Hash:
    def crypt_password(password: str) -> str:
        pwd_context = PasswordHash.recommended()
        return pwd_context.hash(password)

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        pwd_context = PasswordHash.recommended()
        return pwd_context.verify(plain_password, hashed_password)

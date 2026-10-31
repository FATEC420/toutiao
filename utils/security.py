import bcrypt


# 加密（bcrypt 只处理前 72 字节，先按 UTF-8 编码并截断）
def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt())
    return hashed.decode("utf-8")


# 密码校验
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8")[:72],
        hashed_password.encode("utf-8")
    )

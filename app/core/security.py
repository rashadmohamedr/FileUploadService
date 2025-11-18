from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str):
    # bcrypt supports up to 72 bytes — truncate the input, not the output
    password = password[:72]
    return pwd_context.hash(password)

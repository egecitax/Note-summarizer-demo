from passlib.hash import bcrypt

def hash_password(pw:str)->str:
    return bcrypt.hash(pw)
def verify_password(pw:str,h:str)->bool:
    return bcrypt.verify(pw,h)


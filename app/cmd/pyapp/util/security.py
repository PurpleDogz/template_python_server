from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


if __name__ == "__main__":
    logging.getLogger("passlib").setLevel(logging.ERROR)
    print(get_password_hash(""))


def create_apple_key(key_id, team_id, client_id, key):
    headers = {"kid": key_id, "alg": "ES256"}

    payload = {
        "iss": team_id,
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(days=180),
        "aud": "https://appleid.apple.com",
        "sub": client_id,
    }

    client_secret = jwt.encode(payload, key, algorithm="ES256", headers=headers)

    return client_secret

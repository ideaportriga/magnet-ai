import json
from logging import getLogger

from cryptography.fernet import Fernet

from core.config.base import get_general_settings

general_settings = get_general_settings()

SECRET_ENCRYPTION_KEY = general_settings.SECRET_ENCRYPTION_KEY
SECRET_ENCRYPTION_ENCODING = "utf-8"

logger = getLogger(__name__)


def encrypt_secrets(secrets: dict[str, str]) -> str:
    if not SECRET_ENCRYPTION_KEY:
        logger.error("Cannot encrypt secrets - SECRET_ENCRYPTION_KEY is not set.")
        raise Exception()

    fernet = Fernet(SECRET_ENCRYPTION_KEY)
    secrets_string = json.dumps(secrets).encode(SECRET_ENCRYPTION_ENCODING)
    secrets_encrypted = fernet.encrypt(secrets_string).decode(
        SECRET_ENCRYPTION_ENCODING
    )

    return secrets_encrypted


def decrypt_secrets(secrets_encrypted: str) -> dict[str, str]:
    if not SECRET_ENCRYPTION_KEY:
        logger.error("Cannot decrypt secrets - SECRET_ENCRYPTION_KEY is not set.")
        raise Exception()

    fernet = Fernet(SECRET_ENCRYPTION_KEY)
    decrypted_data_str = fernet.decrypt(
        secrets_encrypted.encode(SECRET_ENCRYPTION_ENCODING)
    ).decode(SECRET_ENCRYPTION_ENCODING)

    decrypted_data_dict = json.loads(decrypted_data_str)

    return decrypted_data_dict


def replace_placeholders_in_string(string: str, values: dict[str, str]) -> str:
    """
    Replace placeholders in the form {SECRET_NAME} in the string
    with the corresponding values from the secrets dict.
    Ignores missing secrets.
    """

    for key, value in values.items():
        string = string.replace(f"{{{key}}}", str(value))

    return string


def replace_placeholders_in_dict(data: dict[str, str], values: dict[str, str]) -> dict:
    """
    Replace placeholders in the form {SECRET_NAME} in the values of the data dict
    with the corresponding values from the secrets dict.
    Ignores missing secrets.
    """
    result: dict[str, str] = {}
    for dict_key, dict_value in data.items():
        result[dict_key] = replace_placeholders_in_string(dict_value, values)

    return result

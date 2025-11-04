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


def encrypt_string(value: str) -> str:
    """Encrypt a single string value using Fernet."""
    if not SECRET_ENCRYPTION_KEY:
        logger.error("Cannot encrypt string - SECRET_ENCRYPTION_KEY is not set.")
        raise ValueError("SECRET_ENCRYPTION_KEY is not set. Cannot encrypt value.")

    try:
        fernet = Fernet(SECRET_ENCRYPTION_KEY)
        value = value.encode(SECRET_ENCRYPTION_ENCODING)
        encrypted_value = fernet.encrypt(value).decode(SECRET_ENCRYPTION_ENCODING)
    except ValueError as e:
        logger.error(f"Invalid SECRET_ENCRYPTION_KEY format: {str(e)}")
        raise ValueError(f"Invalid SECRET_ENCRYPTION_KEY format: {str(e)}") from e
    except Exception as e:
        logger.error(f"Failed to encrypt string: {str(e)}")
        raise ValueError(f"Failed to encrypt string: {str(e)}") from e

    return encrypted_value


def decrypt_string(encrypted_value: str) -> str:
    """Decrypt a single string value using Fernet."""
    if not SECRET_ENCRYPTION_KEY:
        logger.error("Cannot decrypt string - SECRET_ENCRYPTION_KEY is not set.")
        raise ValueError("SECRET_ENCRYPTION_KEY is not set. Cannot decrypt value.")

    try:
        fernet = Fernet(SECRET_ENCRYPTION_KEY)
        encrypted_value = encrypted_value.encode(SECRET_ENCRYPTION_ENCODING)
        decrypted_value = fernet.decrypt(encrypted_value).decode(SECRET_ENCRYPTION_ENCODING)
    except ValueError as e:
        logger.error(f"Invalid SECRET_ENCRYPTION_KEY format: {str(e)}")
        raise ValueError(f"Invalid SECRET_ENCRYPTION_KEY format: {str(e)}") from e
    except Exception as e:
        logger.error(f"Failed to decrypt string: {str(e)}")
        raise ValueError(f"Failed to decrypt string: {str(e)}") from e
    return decrypted_value


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
        # Only process string values, keep others as-is
        if isinstance(dict_value, str):
            result[dict_key] = replace_placeholders_in_string(dict_value, values)
        else:
            result[dict_key] = dict_value

    return result

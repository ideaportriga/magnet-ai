from dataclasses import asdict, is_dataclass
from decimal import Decimal
from json import JSONEncoder
from logging import getLogger
from typing import Any

logger = getLogger(__name__)


class DefaultMongoDbSerializer(JSONEncoder):
    def default(self, obj: Any):
        try:
            if isinstance(obj, Decimal):
                return str(obj)

            if is_dataclass(obj):
                return asdict(obj)  # type: ignore

            # Return object type rather than JSONEncoder.default(obj) which simply raises a TypeError
            return f"<{type(obj).__name__}>"
        except Exception as e:
            logger.warning(
                f"Serialization failed for object of type {type(obj).__name__}",
                exc_info=e,
            )
            return f'"<not serializable object of type: {type(obj).__name__}>"'


class OracleDbSerializer(JSONEncoder):
    def default(self, obj: Any):
        if isinstance(obj, Decimal):
            if int(obj) == float(obj):
                return int(obj)
            return float(obj)
        return super().default(obj)

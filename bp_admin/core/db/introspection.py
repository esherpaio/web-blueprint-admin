from typing import Any


def supports_soft_delete(model: Any) -> bool:
    return hasattr(model, "is_deleted")

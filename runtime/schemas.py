from __future__ import annotations

from jsonschema import validate
from jsonschema.exceptions import ValidationError


def validate_input(payload: dict, schema: dict) -> tuple[bool, str | None]:
    try:
        validate(instance=payload, schema=schema)
        return True, None
    except ValidationError as exc:
        return False, str(exc)

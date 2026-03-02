from .exceptions import ValidationError


def validate(instance, schema):
    required = schema.get("required", [])
    for key in required:
        if key not in instance:
            raise ValidationError(f"Missing required property: {key}")

    props = schema.get("properties", {})
    for key, prop in props.items():
        if key not in instance:
            continue
        expected = prop.get("type")
        value = instance[key]
        if expected == "string" and not isinstance(value, str):
            raise ValidationError(f"{key} should be string")
        if expected == "array" and not isinstance(value, list):
            raise ValidationError(f"{key} should be array")
        if expected == "number" and not isinstance(value, (int, float)):
            raise ValidationError(f"{key} should be number")
        if expected == "object" and not isinstance(value, dict):
            raise ValidationError(f"{key} should be object")

        if expected == "array" and "items" in prop and isinstance(value, list):
            item_type = prop["items"].get("type")
            for item in value:
                if item_type == "string" and not isinstance(item, str):
                    raise ValidationError(f"{key} item should be string")
                if item_type == "object" and not isinstance(item, dict):
                    raise ValidationError(f"{key} item should be object")
                if item_type == "object" and isinstance(item, dict):
                    validate(item, prop["items"])

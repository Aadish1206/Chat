import pytest
from jsonschema.exceptions import ValidationError

from core.tools.router import ToolRouter


def test_tool_router_validates_schema_before_execution():
    router = ToolRouter()
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}, "metrics": {"type": "array", "items": {"type": "string"}}},
        "required": ["query", "metrics"],
    }

    with pytest.raises(ValidationError):
        router.execute("NL2SQL_Tool", {"query": "x"}, schema, {})

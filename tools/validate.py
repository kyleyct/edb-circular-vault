#!/usr/bin/env python3
"""
Minimal JSON Schema validator (stdlib only) — supports draft-07 subset.

對應 EDB Circular Bot Project Plan v0.2 §6.4 的 metadata schema 驗證。
不需要 pip install jsonschema，完全 stdlib compatible。

支援 keywords:
- type (string / integer / number / boolean / array / object / null, or list of types)
- required
- properties + additionalProperties (bool or schema)
- items
- enum
- const
- pattern (regex)
- minLength, maxLength
- minimum, maximum
- minItems, maxItems
- format: "date", "date-time", "uri", "email"

Usage:
    from validate import validate
    errors = validate(instance, schema)
    if errors:
        for e in errors:
            print(f"  - {e}")
"""
import re
import sys
import json
from typing import Any

# Format checkers
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$")
_URI_RE = re.compile(r"^https?://", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_type(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_check_type(value, t) for t in expected)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "null":
        return value is None
    return True


def _check_format(value: str, fmt: str) -> bool:
    if fmt == "date":
        return bool(_DATE_RE.match(value))
    if fmt == "date-time":
        return bool(_DATETIME_RE.match(value))
    if fmt == "uri":
        return bool(_URI_RE.match(value))
    if fmt == "email":
        return bool(_EMAIL_RE.match(value))
    return True  # unknown format = pass


def validate(instance: Any, schema: dict, path: str = "$") -> list:
    """Validate instance against schema. Return list of error messages."""
    errors = []
    if not isinstance(schema, dict):
        return errors

    # type
    if "type" in schema:
        if not _check_type(instance, schema["type"]):
            errors.append(f"{path}: expected type {schema['type']}, got {type(instance).__name__}")
            return errors  # 不再繼續 validate（type 錯）

    # enum
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum {schema['enum']}")

    # const
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: value {instance!r} != const {schema['const']!r}")

    # string constraints
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: string length {len(instance)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: string length {len(instance)} > maxLength {schema['maxLength']}")
        if "pattern" in schema:
            try:
                if not re.search(schema["pattern"], instance):
                    errors.append(f"{path}: string {instance[:50]!r} does not match pattern {schema['pattern']!r}")
            except re.error as e:
                errors.append(f"{path}: invalid pattern in schema: {e}")
        if "format" in schema and not _check_format(instance, schema["format"]):
            errors.append(f"{path}: string {instance[:80]!r} does not match format {schema['format']!r}")

    # number constraints
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: value {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: value {instance} > maximum {schema['maximum']}")

    # array constraints
    if isinstance(instance, list):
        if "items" in schema:
            for i, item in enumerate(instance):
                errors.extend(validate(item, schema["items"], f"{path}[{i}]"))
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: array length {len(instance)} < minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: array length {len(instance)} > maxItems {schema['maxItems']}")

    # object constraints
    if isinstance(instance, dict):
        if "required" in schema:
            for req in schema["required"]:
                if req not in instance:
                    errors.append(f"{path}: missing required field '{req}'")

        if "properties" in schema:
            for key, value in instance.items():
                if key in schema["properties"]:
                    errors.extend(validate(value, schema["properties"][key], f"{path}.{key}"))
                else:
                    ap = schema.get("additionalProperties", True)
                    if ap is False:
                        errors.append(f"{path}: unexpected field '{key}' (additionalProperties: false)")
                    elif isinstance(ap, dict):
                        errors.extend(validate(value, ap, f"{path}.{key}"))

    return errors


def validate_file(schema_path: str, instance_path: str) -> tuple:
    """Validate JSON file against schema file. Return (valid, errors, schema, instance)."""
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    with open(instance_path, encoding="utf-8") as f:
        instance = json.load(f)
    errors = validate(instance, schema)
    return (len(errors) == 0, errors, schema, instance)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate.py <schema.json> <instance.json>", file=sys.stderr)
        sys.exit(2)
    valid, errors, _, _ = validate_file(sys.argv[1], sys.argv[2])
    if valid:
        print(f"OK: {sys.argv[2]} validates against {sys.argv[1]}")
        sys.exit(0)
    else:
        print(f"FAIL ({len(errors)} error(s)):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

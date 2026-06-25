"""
JSON Response customizado para o dIAloga+.

Adiciona automaticamente o timezone UTC ('Z') aos datetimes.
O SQLite remove timezone info, entao precisamos garantir que
o frontend saiba que a data esta em UTC.
"""
import json
import re
from datetime import datetime, timezone
from fastapi.responses import JSONResponse


# Regex para detectar strings ISO de datetime (sem timezone)
ISO_DATETIME_RE = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$'
)


def fix_datetime_string(s):
    """Se a string parece ISO datetime sem timezone, adiciona 'Z' (UTC)."""
    if isinstance(s, str) and ISO_DATETIME_RE.match(s):
        return s + "Z"
    return s


def fix_datetimes(obj):
    """Converte recursivamente strings ISO datetime adicionando 'Z'."""
    if isinstance(obj, dict):
        return {k: fix_datetimes(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [fix_datetimes(v) for v in obj]
    if isinstance(obj, str):
        return fix_datetime_string(obj)
    return obj


class CustomJSONResponse(JSONResponse):
    """JSONResponse que adiciona 'Z' (UTC) aos datetimes sem timezone."""

    def render(self, content):
        converted = fix_datetimes(content)
        return json.dumps(
            converted,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

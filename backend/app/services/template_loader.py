"""
Serviço para carregar templates JSON do diretório /templates.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from ..models import Template

logger = logging.getLogger("dialoga.templates")

# Diretórios onde os templates JSON podem estar
TEMPLATE_DIRS = [
    Path(__file__).parent.parent.parent.parent / "templates",  # raiz /templates
    Path(__file__).parent / "templates_data",                    # backend/app/templates_data
]


def _find_template_dir() -> Path:
    """Encontra o primeiro diretório de templates que existe."""
    for d in TEMPLATE_DIRS:
        if d.exists():
            return d
    raise FileNotFoundError(
        "Diretório de templates não encontrado. Esperado em /templates ou backend/app/templates_data"
    )


def load_all_template_files() -> List[Dict[str, Any]]:
    """Lê todos os arquivos JSON de templates."""
    base = _find_template_dir()
    templates = []
    for path in sorted(base.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_file"] = path.name
                templates.append(data)
        except Exception as e:
            logger.error("Erro ao ler template %s: %s", path, e)
    return templates


def seed_templates(db: Session) -> int:
    """
    Insere templates no banco se ainda não existirem.
    Atualiza os existentes caso os arquivos tenham mudado.
    Retorna quantidade de templates inseridos.
    """
    try:
        files = load_all_template_files()
    except FileNotFoundError as e:
        logger.warning(str(e))
        return 0

    inserted = 0

    for tpl in files:
        slug = tpl.get("slug")
        if not slug:
            logger.warning("Template sem slug em %s - ignorado", tpl.get("_file"))
            continue

        existing = db.query(Template).filter(Template.slug == slug).first()

        if existing:
            # Atualiza dados caso o arquivo tenha mudado
            existing.name = tpl.get("name", existing.name)
            existing.description = tpl.get("description", existing.description)
            existing.category = tpl.get("category", existing.category)
            existing.icon = tpl.get("icon", existing.icon)
            existing.flow_data = tpl.get("nodes", tpl.get("flow_data", []))
            continue

        db.add(
            Template(
                slug=slug,
                name=tpl.get("name", slug),
                description=tpl.get("description", ""),
                category=tpl.get("category", "Geral"),
                icon=tpl.get("icon", "🤖"),
                flow_data=tpl.get("nodes", tpl.get("flow_data", [])),
            )
        )
        inserted += 1

    # BUGFIX: commit sempre, mesmo se só houver updates (antes estava dentro do if inserted)
    db.commit()

    if inserted:
        logger.info("%d templates inseridos no banco", inserted)

    return inserted
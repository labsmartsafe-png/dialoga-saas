"""
Smoke/regression checks for dIAloga+.

Run from project root:
    python backend/scripts/regression_smoke.py

This script intentionally avoids importing the full FastAPI app, because production
settings/env vars may not exist locally. It validates the most common regressions:
- Python syntax under backend/app
- JS syntax for frontend/js/*.js when Node is available
- injected external scripts in frontend/*.html
- required key files exist
"""
from __future__ import annotations

import compileall
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_APP = ROOT / "backend" / "app"
FRONTEND = ROOT / "frontend"

BAD_HTML_PATTERNS = [
    "kaspersky",
    "cloudflareinsights",
    "cdn-cgi",
    "challenge-platform",
]

REQUIRED_FILES = [
    "backend/app/main.py",
    "backend/app/models.py",
    "backend/app/database.py",
    "backend/app/routers/admin.py",
    "backend/app/routers/billing.py",
    "backend/app/routers/whatsapp_evolution.py",
    "backend/app/services/flow_engine.py",
    "backend/app/services/lead_service.py",
    "frontend/js/api.js",
    "frontend/js/auth.js",
    "frontend/js/config.js",
    "frontend/js/layout.js",
    "frontend/dashboard.html",
    "frontend/builder.html",
    "frontend/leads.html",
    "frontend/inbox.html",
    "frontend/agenda.html",
    "frontend/ia.html",
    "frontend/configuracoes.html",
]


def ok(msg: str):
    print(f"[OK] {msg}")


def fail(msg: str):
    print(f"[FAIL] {msg}")


def check_required_files() -> bool:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    if missing:
        fail("Arquivos obrigatórios ausentes:\n  " + "\n  ".join(missing))
        return False
    ok("arquivos obrigatórios presentes")
    return True


def check_python_syntax() -> bool:
    success = compileall.compile_dir(str(BACKEND_APP), quiet=1, force=True)
    if success:
        ok("sintaxe Python em backend/app")
    else:
        fail("erro de sintaxe Python em backend/app")
    return bool(success)


def check_js_syntax() -> bool:
    node = shutil.which("node")
    if not node:
        print("[WARN] Node não encontrado; pulando validação JS")
        return True
    js_files = sorted((FRONTEND / "js").glob("*.js"))
    good = True
    for js in js_files:
        proc = subprocess.run([node, "--check", str(js)], cwd=str(ROOT), text=True, capture_output=True)
        if proc.returncode != 0:
            good = False
            fail(f"erro JS em {js.relative_to(ROOT)}:\n{proc.stderr or proc.stdout}")
    if good:
        ok("sintaxe JS em frontend/js")
    return good


def check_injected_scripts() -> bool:
    offenders: list[str] = []
    for html in sorted(FRONTEND.glob("*.html")):
        text = html.read_text(encoding="utf-8", errors="ignore").lower()
        for pat in BAD_HTML_PATTERNS:
            if pat in text:
                offenders.append(f"{html.relative_to(ROOT)} contém {pat}")
    if offenders:
        fail("scripts externos injetados encontrados:\n  " + "\n  ".join(offenders))
        return False
    ok("HTMLs sem scripts externos injetados")
    return True


def main() -> int:
    checks = [
        check_required_files(),
        check_python_syntax(),
        check_js_syntax(),
        check_injected_scripts(),
    ]
    if all(checks):
        print("\nSmoke/regression básico concluído com sucesso.")
        return 0
    print("\nSmoke/regression encontrou problemas.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

# Executa limpeza de HTML e smoke test básico.
# Uso, na raiz do projeto:
#   powershell -ExecutionPolicy Bypass -File .\scripts\validar-regressao.ps1
# ou:
#   .\scripts\validar-regressao.ps1

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== Limpando scripts externos dos HTMLs =="
powershell -ExecutionPolicy Bypass -File ".\scripts\limpar-html.ps1"

Write-Host ""
Write-Host "== Rodando smoke/regression =="
python backend/scripts/regression_smoke.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "Smoke/regression encontrou problemas. Corrija antes de commitar."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Validação concluída com sucesso."

# Limpa scripts externos injetados nos HTMLs do frontend.
# Uso, na raiz do projeto:
#   powershell -ExecutionPolicy Bypass -File .\scripts\limpar-html.ps1
# ou, se a política permitir:
#   .\scripts\limpar-html.ps1

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root "frontend"

if (-not (Test-Path $frontend)) {
    Write-Error "Pasta frontend não encontrada em: $frontend"
    exit 1
}

$files = Get-ChildItem $frontend -Filter *.html
$changed = 0

foreach ($file in $files) {
    $path = $file.FullName
    $original = Get-Content $path -Raw -Encoding UTF8
    $content = $original

    # Remove Cloudflare Insights / beacon
    $content = [regex]::Replace(
        $content,
        '(?is)<script\b[^>]*src=["''][^"'']*cloudflareinsights\.com[^"'']*["''][^>]*>.*?</script>\s*',
        ''
    )

    # Remove Cloudflare challenge / cdn-cgi
    $content = [regex]::Replace(
        $content,
        '(?is)<script>\(function\(\)\{function c\(\).*?challenge-platform/scripts/jsd/main\.js.*?</script>\s*',
        ''
    )

    # Remove Kaspersky, se aparecer
    $content = [regex]::Replace(
        $content,
        '(?is)<script\b[^>]*kaspersky-labs\.com[^>]*>.*?</script>\s*',
        ''
    )

    if ($content -ne $original) {
        Set-Content -Path $path -Value $content -Encoding UTF8
        $changed += 1
        Write-Host "Limpo: $($file.Name)"
    }
}

Write-Host "Limpeza de HTML concluída. Arquivos alterados: $changed"

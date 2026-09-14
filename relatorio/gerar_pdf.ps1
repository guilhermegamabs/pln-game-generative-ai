# Gera o PDF único de entrega do CP4 a partir de relatorio.html.
# Uso (na pasta POC):  powershell -ExecutionPolicy Bypass -File relatorio\gerar_pdf.ps1

$dir = $PSScriptRoot
$poc = Split-Path $dir -Parent
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$python = 'F:\ia-local\venv\Scripts\python.exe'
$saida = Join-Path $poc 'OS_7_PECADOS_CP4.pdf'

# PNGs originais somam ~20 MB; em JPG 1600 px o PDF fica leve sem perda visível na impressão.
& $python -c @"
from pathlib import Path
from PIL import Image
poc = Path(r'$poc'); destino = poc / 'relatorio' / 'img'; destino.mkdir(exist_ok=True)
fontes = list((poc / 'assets' / 'imagens').glob('*.png')) + list((poc / 'mockup').glob('*_anotado.png'))
for f in fontes:
    im = Image.open(f).convert('RGB'); im.thumbnail((1600, 1600)); im.save(destino / (f.stem + '.jpg'), quality=84)
print(len(fontes), 'imagens preparadas')
"@

$url = 'file:///' + ($dir -replace '\\', '/') + '/relatorio.html'
if (Test-Path $saida) { Remove-Item -LiteralPath $saida }
Start-Process -FilePath $edge -WindowStyle Hidden -ArgumentList @(
    '--headless=new', '--disable-gpu', "--user-data-dir=$env:TEMP\os7pecados-edge-pdf",
    '--allow-file-access-from-files', '--no-pdf-header-footer', '--virtual-time-budget=15000',
    "--print-to-pdf=$saida", "`"$url`""
)
$espera = 0
while (-not (Test-Path $saida) -and $espera -lt 120) { Start-Sleep -Milliseconds 500; $espera++ }
Start-Sleep -Seconds 2
Write-Output ("PDF: {0} ({1:N1} MB)" -f $saida, ((Get-Item $saida).Length / 1MB))

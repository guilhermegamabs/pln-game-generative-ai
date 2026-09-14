# Exporta as 3 telas do mockup (limpa e anotada) em PNG 1920x1080 usando o Edge headless.
# Uso (na pasta POC):  powershell -ExecutionPolicy Bypass -File mockup\exportar.ps1

$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$dir = $PSScriptRoot
$url = 'file:///' + ($dir -replace '\\', '/') + '/mockup.html'
$perfil = Join-Path $env:TEMP 'os7pecados-edge'

$telas = @(
    @('menu', '1_menu'),
    @('gameplay', '2_gameplay'),
    @('espelho', '3_espelho_da_alma')
)

$i = 0
foreach ($t in $telas) {
    foreach ($anotado in @($false, $true)) {
        $i++
        $sufixo = if ($anotado) { '_anotado' } else { '' }
        $query = "?tela=$($t[0])" + $(if ($anotado) { '&anotado=1' } else { '' })
        $png = Join-Path $dir "$($t[1])$sufixo.png"
        if (Test-Path $png) { Remove-Item -LiteralPath $png }

        # O launcher do Edge retorna antes do screenshot ficar pronto e instâncias paralelas
        # disputam o perfil: cada tela usa um perfil próprio e esperamos o arquivo aparecer.
        Start-Process -FilePath $edge -WindowStyle Hidden -ArgumentList @(
            '--headless=new', '--disable-gpu', '--hide-scrollbars',
            "--user-data-dir=$perfil$i", '--allow-file-access-from-files',
            '--window-size=1920,1080', '--virtual-time-budget=8000',
            "--screenshot=$png", "`"$url$query`""
        )
        $espera = 0
        while (-not (Test-Path $png) -and $espera -lt 60) { Start-Sleep -Milliseconds 500; $espera++ }
        Start-Sleep -Seconds 1
        Write-Output ("{0} {1:N0} KB" -f (Split-Path $png -Leaf), ((Get-Item $png).Length / 1KB))
    }
}

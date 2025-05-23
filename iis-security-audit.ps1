# Verificação de Segurança para Servidor IIS
# Execute como Administrador

# 1. Verificar versão do IIS e módulos instalados
Write-Host "`n[+] Informações do IIS`n" -ForegroundColor Cyan
Get-ItemProperty HKLM:\SOFTWARE\Microsoft\InetStp\ | Select-Object VersionString

# 2. Verificar configurações de SSL/TLS
Write-Host "`n[+] Verificando protocolos SSL/TLS`n" -ForegroundColor Cyan

$protocols = @(
    'SSL 2.0',
    'SSL 3.0',
    'TLS 1.0',
    'TLS 1.1',
    'TLS 1.2',
    'TLS 1.3'
)

foreach ($protocol in $protocols) {
    $keyPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$protocol\Server"
    if (Test-Path $keyPath) {
        $enabled = (Get-ItemProperty -Path $keyPath -Name Enabled).Enabled
        $status = if ($enabled -eq 0) {"DESATIVADO"} else {"ATIVADO"}
        Write-Host "$protocol : $status" -ForegroundColor $(if ($enabled -eq 0) { "Green" } else { "Red" })
    }
}

# 3. Verificar headers de segurança
Write-Host "`n[+] Verificando Headers de Segurança HTTP`n" -ForegroundColor Cyan

$headersToCheck = @(
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Content-Security-Policy",
    "Referrer-Policy",
    "Permissions-Policy"
)

try {
    $response = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing
    foreach ($header in $headersToCheck) {
        $exists = $response.Headers[$header] -ne $null
        Write-Host "$header : $(if ($exists) {'OK'} else {'FALTANDO'})" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
    }
}
catch {
    Write-Host "Erro ao verificar headers: $_" -ForegroundColor Red
}

# 4. Verificar autenticação
Write-Host "`n[+] Verificando Métodos de Autenticação`n" -ForegroundColor Cyan

Get-WebConfigurationProperty -Filter "/system.webServer/security/authentication/*" -Name enabled -Location "Default Web Site" | 
Where-Object { $_.Value -eq $true } | 
Format-Table -Property @{Name='Authentication';Expression={$_.ItemXPath.Split('/')[-1]}}, Value

# 5. Verificar logging
Write-Host "`n[+] Verificando Configurações de Log`n" -ForegroundColor Cyan

$logSettings = Get-WebConfigurationProperty -Filter "system.applicationHost/sites/siteDefaults" -Name logFile
Write-Host "Logging Ativado: $($logSettings.enabled)"
Write-Host "Diretório de Logs: $($logSettings.directory)"
Write-Host "Período de Rotação: $($logSettings.period)"

# 6. Verificar atualizações
Write-Host "`n[+] Verificando Atualizações de Segurança`n" -ForegroundColor Cyan

$hotfixes = Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10
Write-Host "Últimas 10 atualizações instaladas:"
$hotfixes | Format-Table -Property HotFixID, InstalledOn, Description

# 7. Verificar features desnecessárias
Write-Host "`n[+] Verificando Features Opcionais Instaladas`n" -ForegroundColor Cyan

$features = Get-WindowsFeature | Where-Object { $_.Installed -eq $true }
$riskyFeatures = @(
    "Web-Ftp-Server",
    "Web-CGI",
    "Web-Server",
    "Web-ASP"
)

foreach ($feature in $features) {
    if ($feature.Name -in $riskyFeatures) {
        Write-Host "$($feature.Name) : INSTALADO" -ForegroundColor Red
    }
}

# Resumo
Write-Host "`n[+] Resumo de Verificação`n" -ForegroundColor Yellow
Write-Host "1. Protocolos inseguros ativados? $(if ($protocols.Where({$_.Status -eq 'ATIVADO'}).Count -gt 0) {'SIM'} else {'NÃO'})"
Write-Host "2. Headers de segurança ausentes? $(if ($headersToCheck.Where({$response.Headers[$_] -eq $null}).Count -gt 0) {'SIM'} else {'NÃO'})"
Write-Host "3. Autenticação básica habilitada? $(if (Get-WebConfigurationProperty -Filter "/system.webServer/security/authentication/basicAuthentication" -Name enabled -Location "Default Web Site").Value) {'SIM'} else {'NÃO'})"
Write-Host "4. Features de risco instaladas? $(if ($features.Where({$_.Name -in $riskyFeatures -and $_.Installed}).Count -gt 0) {'SIM'} else {'NÃO'})"

Write-Host "`n[!] Recomendações:" -ForegroundColor Yellow
Write-Host "- Desative protocolos SSL 2.0/3.0 e TLS 1.0/1.1"
Write-Host "- Configure headers de segurança faltantes via web.config"
Write-Host "- Atualize o servidor regularmente"
Write-Host "- Remova features não utilizadas"

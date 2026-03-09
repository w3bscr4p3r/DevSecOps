# CheckVulnWin.ps1 - Verificação de Vulnerabilidades Windows 10/11
$Report = @()
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$ComputerName = $env:COMPUTERNAME
$OS = (Get-WmiObject Win32_OperatingSystem).Caption

# 1. Patches/Hotfixes
$Hotfixes = Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5
$PatchStatus = if ($Hotfixes) { "OK - Últimos: $($Hotfixes[0].HotFixID)" } else { "ALERTA - Sem patches" }
$Report += [PSCustomObject]@{Categoria="Patches"; Status=$PatchStatus; Detalhes=$Hotfixes.HotFixID -join ", "}

# 2. Firewall
$Firewall = Get-NetFirewallProfile | Select-Object Name, Enabled
$FWStatus = ($Firewall | Where-Object Enabled -eq True).Count -eq 3 ? "OK" : "ALERTA - Perfil desabilitado"
$Report += [PSCustomObject]@{Categoria="Firewall"; Status=$FWStatus; Detalhes=($Firewall | ForEach-Object "$($_.Name): $($_.Enabled)" -join "; ")}

# 3. Windows Defender (Win10/11)
try {
    $Defender = Get-MpComputerStatus
    $AVStatus = if ($Defender.AMServiceEnabled -and $Defender.IsTamperProtected) { "OK" } else { "ALERTA" }
} catch {
    $AVStatus = "N/A - Cmdlet indisponível"
}
$Report += [PSCustomObject]@{Categoria="Antivírus"; Status=$AVStatus; Detalhes="Real-time: $($Defender.AMRunningMode)"}

# 4. Usuários Locais
$Users = Get-LocalUser | Where-Object Enabled -eq True | Select-Object Name, LastLogon
$UserStatus = if ($Users.Count -le 2) { "OK" } else { "ALERTA - Muitos usuários" }
$Report += [PSCustomObject]@{Categoria="Usuários"; Status=$UserStatus; Detalhes=($Users.Name -join ", ")}

# 5. UAC e Políticas
$UAC = Get-ItemProperty 'HKLM:SOFTWAREMicrosoftWindowsCurrentVersionPoliciesSystem' -Name EnableLUA -ErrorAction SilentlyContinue
$UACStatus = if ($UAC.EnableLUA -eq 1) { "OK" } else { "ALERTA - UAC desabilitado" }
$Report += [PSCustomObject]@{Categoria="UAC"; Status=$UACStatus; Detalhes="EnableLUA: $($UAC.EnableLUA)"}

# 6. RDP
$RDP = Get-ItemProperty 'HKLM:SystemCurrentControlSetControlTerminal Server' -Name fDenyTSConnections
$RDPStatus = if ($RDP.fDenyTSConnections -eq 1) { "OK - Desabilitado" } else { "ALERTA - RDP exposto" }
$Report += [PSCustomObject]@{Categoria="RDP"; Status=$RDPStatus; Detalhes="fDenyTSConnections: $($RDP.fDenyTSConnections)"}

# 7. Execution Policy
$ExecPolicy = Get-ExecutionPolicy
$ExecStatus = if ($ExecPolicy -eq "Restricted") { "OK" } else { "ALERTA - Scripts perigosos" }
$Report += [PSCustomObject]@{Categoria="ExecPolicy"; Status=$ExecStatus; Detalhes=$ExecPolicy}

# Gerar Relatório HTML
$Report | Export-Csv -Path "VulnReport_$ComputerName.csv" -NoTypeInformation -Encoding UTF8
$HTML = $Report | ConvertTo-Html -Property Categoria,Status,Detalhes -Head "<title>Relatório Vulnerabilidades $Timestamp</title>"
$HTML | Out-File "VulnReport_$ComputerName.html"
Write-Output "Relatórios gerados: VulnReport_$ComputerName.{csv,html}"
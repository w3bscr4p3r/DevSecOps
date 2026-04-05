# DevSecOps

Ferramentas de auditoria de segurança, OSINT e análise de vulnerabilidades.

## Ferramentas

### OSINT e Análise de IPs

| Ferramenta | Descrição |
|------------|-----------|
| `ip_analyzer_v2.py` | Interface GUI (PySimpleGUI) para consulta de reputação de IPs usando AbuseIPDB e Shodan. Armazena histórico em SQLite. |
| `malicious_ip_finder_v2.py` | Ferramenta de terminal para detecção de IPs maliciosos usando a API do Shodan. |
| `smb_vuln_detect.py` | Scanner de versão SMB que identifica SMBv1/v2/v3 e verifica vulnerabilidades como EternalBlue. |

### Scanners de Vulnerabilidade

| Ferramenta | Descrição |
|------------|-----------|
| `check_vuln_linux.sh` | Scanner multi-distribuição (Ubuntu/Debian/RHEL/CentOS/Fedora/SUSE/Arch/Alpine). Verifica atualizações, CVEs via Trivy e hardening. Saída: JSON. |
| `check_vuln_win.ps1` | Auditor para Windows 10/11. Verifica patches, firewall, Windows Defender, UAC, RDP e políticas. Saída: CSV/HTML. |
| `iis-security-audit.ps1` | Auditor de servidores IIS. Verifica protocolos SSL/TLS, headers de segurança, autenticação e logging. |

### SAST/DAST

| Ferramenta | Descrição |
|------------|-----------|
| `SAST-DAST/toolkit.py` | Scanner de segurança com análise estática (Bandit) e verificação de dependências (Safety). Módulo DAST testa SQL injection e headers. |

## Instalação

```bash
# Instalar dependências gerais
pip install shodan impacket requests beautifulsoup4 pysimplegui

# Para SAST/DAST
cd SAST-DAST
pip install bandit safety pyyaml
```

## Uso

### OSINT Tools (requer chaves de API)

```bash
export ABUSEIPDB_KEY="sua_chave" SHODAN_KEY="sua_chave"

# Analisador de IPs com GUI
python ip_analyzer_v2.py

# Detector de IPs maliciosos (terminal)
python malicious_ip_finder_v2.py

# Scanner SMB
python smb_vuln_detect.py <IP_ALVO> --json
```

### Scanners de Vulnerabilidade

```bash
# Linux (requer sudo)
sudo bash check_vuln_linux.sh

# Windows (PowerShell como Administrador)
powershell -ExecutionPolicy Bypass -File check_vuln_win.ps1

# IIS Audit (PowerShell)
powershell -ExecutionPolicy Bypass -File iis-security-audit.ps1
```

### SAST/DAST

```bash
cd SAST-DAST

# Análise estática de código Python
python toolkit.py --sast /caminho/do/projeto

# Teste dinâmico em API web
python toolkit.py --dast http://localhost:8000
```

## Avisos Legais

> **IMPORTANTE:** Estas ferramentas são destinadas apenas para:
> - Testes de penetração autorizados
> - Auditorias de segurança em sistemas próprios
> - Fins educacionais e de pesquisa
>
> O uso não autorizado em sistemas de terceiros é ilegal e pode constituir crime.

## Documentação Adicional

- [The Gentlemen Ransomware](theGentlemenRansoware.md) - Estudo de caso sobre ransomware

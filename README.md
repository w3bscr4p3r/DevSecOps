# DevSecOps

Coleção de ferramentas para auditoria de segurança, OSINT, análise de infraestrutura e revisão de aplicações.

O repositório reúne scripts para:
- mapear reputação e metadados de IPs/domínios;
- verificar versões e riscos de SMB;
- auditar sistemas Linux, Windows e IIS;
- executar análise estática e dinâmica de segurança em projetos de software.

As ferramentas aqui presentes são direcionadas para ambientes próprios, testes autorizados e pesquisa de segurança em contextos legais e aprovados.

## Visão geral por categoria

### OSINT e análise de IPs

| Script | Descrição |
|---|---|
| `ip_analyzer_v2.py` | Interface gráfica em Tkinter para consultar AbuseIPDB, Shodan e VirusTotal sobre IPs/domínios. Possui persistência em SQLite. |
| `malicious_ip_finder_v2.py` | Ferramenta de terminal para processar listas de IPs e exportar resultados em CSV com análise de reputação. |
| `smb_vuln_detect.py` | Scanner de SMB para detectar versão negociada, estado da porta 445 e mensagens de risco associadas a SMBv1/v2/v3. |

### Scanners de vulnerabilidade

| Script | Descrição |
|---|---|
| `check_vuln_linux.sh` | Scanner multi-distro para Linux (Ubuntu/Debian/RHEL/CentOS/Fedora/SUSE/Arch/Alpine). Verifica atualizações, CVEs com Trivy e hardening do host. Saída em JSON. |
| `check_vuln_win.ps1` | Auditor de Windows 10/11 para patches, firewall, Defender, UAC, políticas e RDP. Gera CSV/HTML. |
| `iis-security-audit.ps1` | Auditor de IIS para SSL/TLS, headers HTTP, autenticação, logs e features instaladas. |

### SAST/DAST

| Script | Descrição |
|---|---|
| `SAST-DAST/toolkit.py` | Ferramenta para análise estática com Bandit e validação de dependências com Safety; também suporta testes dinâmicos contra APIs web. |

## Requisitos

### Dependências gerais (Python)

```bash
python -m pip install --upgrade pip
python -m pip install requests shodan impacket PySimpleGUI beautifulsoup4
```

### Dependências para SAST/DAST

```bash
cd SAST-DAST
python -m pip install bandit safety pyyaml
```

### Dependências para Linux scanner

```bash
sudo apt-get update
sudo apt-get install jq curl
```

O script `check_vuln_linux.sh` também tenta baixar o Trivy automaticamente quando necessário.

## Variáveis de ambiente

Os scripts de OSINT utilizam credenciais de API. Configure-as antes de executar:

```bash
export ABUSEIPDB_API_KEY="sua_chave"
export SHODAN_KEY="sua_chave"
export VIRUSTOTAL_API_KEY="sua_chave"
```

O arquivo `ip_analyzer_v2.py` e o `malicious_ip_finder_v2.py` devem ser executados somente com chaves válidas e com as permissões adequadas para acesso externo.

## Uso

### 1) OSINT e análise de IPs

```bash
# GUI para consulta de reputação
python ip_analyzer_v2.py

# Processamento em lote de vários IPs a partir de CSV
python malicious_ip_finder_v2.py

# Detecção de versão SMB e risco de vulnerabilidade
python smb_vuln_detect.py 192.168.1.10 --json
```

### 2) Scanners de vulnerabilidade

```bash
# Linux (requer privilégios de administrador/root)
sudo bash check_vuln_linux.sh

# Windows 10/11 (PowerShell como administrador)
powershell -ExecutionPolicy Bypass -File check_vuln_win.ps1

# IIS (PowerShell como administrador)
powershell -ExecutionPolicy Bypass -File iis-security-audit.ps1
```

### 3) SAST/DAST

```bash
cd SAST-DAST

# Análise estática em um projeto Python
python toolkit.py --sast /caminho/do/projeto

# Teste dinâmico contra uma API em execução
python toolkit.py --dast http://localhost:8000
```

## Estrutura do projeto

```text
.
├── README.md
├── LICENSE
├─�� SAST-DAST/
│   ├── README.md
│   └── toolkit.py
├── ip_analyzer_v2.py
├── malicious_ip_finder_v2.py
├── smb_vuln_detect.py
├── check_vuln_linux.sh
├── check_vuln_win.ps1
├── iis-security-audit.ps1
└── tools and scan outputs generated at runtime
```

## Observações importantes

- Não é recomendável executar os scanners contra alvos sem autorização explícita.
- Os scripts de rede e OSINT podem gerar tráfego e consultas em serviços externos; valide sempre o escopo antes de usar.
- O projeto não substitui políticas, requisitos legais ou procedimentos internos de segurança.
- Em ambientes Windows, alguns módulos dependem de cmdlets específicos e do contexto de administrador.

## Aviso legal

> Este repositório foi criado para fins de pesquisa, educação, hardening e auditoria em ambientes próprios ou autorizados.
>
> O uso não autorizado em sistemas de terceiros pode ser ilegal e violar leis locais e internacionais.
>
> Sempre obtenha autorização antes de escanear, testar ou auditar qualquer infraestrutura que não seja de sua propriedade ou responsabilidade formal.

## Contribuição

Contribuições, correções e melhorias são bem-vindas. Sugestões de hardening, testes automatizados e refatorações de segurança podem ser enviadas por pull request, com foco em segurança, clareza e manutenção do código.

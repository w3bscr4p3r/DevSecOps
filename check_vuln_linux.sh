#!/bin/bash
# =============================================================================
# Linux Vulnerability Master Scanner v2.0
# Suporte: Debian/Ubuntu/RHEL/CentOS/Fedora/SUSE/Alpine/Arch/Mint/Amazon
# =============================================================================

set -euo pipefail

# Cores e logging
RED='\u001B[0;31m'; GREEN='\u001B[0;32m'; YELLOW='\u001B[1;33m'; NC='\u001B[0m'
LOG_FILE="vuln-master-$(date +%Y%m%d-%H%M).json"
HOSTNAME=$(hostname)
TIMESTAMP=$(date -Iseconds)

# Função: Detecta distro e gerenciador
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID$VERSION_ID" | tr '[:upper:]' '[:lower:]' | tr -d '"'
    elif [ -f /etc/redhat-release ]; then
        cat /etc/redhat-release | cut -d' ' -f1 | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown"
    fi
}

# Função: Header JSON
init_report() {
    cat > "$LOG_FILE" << EOF
{
  "scan": {
    "host": "$HOSTNAME",
    "timestamp": "$TIMESTAMP",
    "distro": "$(detect_distro)",
    "cves": {},
    "security_updates": 0,
    "risks": [],
    "score": 0
  }
}
EOF
}

# Função: Security Updates por distro
check_security_updates() {
    local distro=$(detect_distro)
    local count=0
    
    case "$distro" in
        ubuntu|debian*)
            sudo apt update -qq 2>/dev/null
            count=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
            echo "Security updates (APT): $count"
            ;;
        fedora*)
            count=$(sudo dnf check-update --security 2>/dev/null | grep -v '^$' | wc -l)
            echo "Security updates (DNF): $count"
            ;;
        rhel|centos|ol*)
            if command -v dnf >/dev/null; then
                count=$(sudo dnf updateinfo list security installed 2>/dev/null | grep -c '^.*: ')
            else
                count=$(sudo yum check-update --security 2>/dev/null | wc -l)
            fi
            echo "Security updates (YUM/DNF): $count"
            ;;
        suse*|opensuse*)
            count=$(sudo zypper lu -t security 2>/dev/null | grep -c '^S  ')
            echo "Security updates (Zypper): $count"
            ;;
        alpine*)
            count=$(sudo apk update && apk list --upgradable | wc -l)
            echo "Security updates (APK): $count"
            ;;
        arch*)
            count=$(sudo pacman -Qu | wc -l)
            echo "Security updates (Pacman): $count"
            ;;
        amazon*)
            count=$(sudo yum check-update --security 2>/dev/null | wc -l)
            echo "Security updates (Amazon): $count"
            ;;
        *)
            echo "Security updates: N/A (distro não suportada)"
            ;;
    esac
    
    jq ".scan.security_updates = $count" "$LOG_FILE" > tmp && mv tmp "$LOG_FILE"
}

# Função: Instala Trivy universal
install_trivy() {
    if ! command -v trivy >/dev/null; then
        echo -e "${YELLOW}Instalando Trivy...${NC}"
        if command -v curl >/dev/null; then
            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
        else
            echo -e "${RED}Curl não encontrado. Trivy pulado.${NC}"
            return 1
        fi
    fi
}

# Função: Scan CVEs com Trivy
scan_cves() {
    install_trivy || return 1
    
    echo -e "${YELLOW}=== Scanning CVEs (HIGH/CRITICAL) ===${NC}"
    trivy fs / --severity HIGH,CRITICAL --format json --output trivy.json >/dev/null 2>&1
    
    local critical=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' trivy.json)
    local high=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity=="HIGH")] | length' trivy.json)
    
    jq ".scan.cves |= {"critical": $critical, "high": $high}" "$LOG_FILE" > tmp && mv tmp "$LOG_FILE"
    
    echo "CVEs CRITICAL: $critical | HIGH: $high"
    trivy fs / --severity HIGH,CRITICAL --format table | head -10
}

# Função: Hardening checks universais
check_hardening() {
    local risks=()
    
    # World writable files
    if find / -xdev -type f -perm -o+w 2>/dev/null | head -5 | grep -q .; then
        risks+=("world_writable_files")
        echo -e "${RED}❌ World-writable files encontrados${NC}"
    fi
    
    # SUID/SGID excessivos
    if find / -xdev ( -perm -4000 -o -perm -2000 ) -type f 2>/dev/null | wc -l | grep -q ">[1-9][0-9]*"; then
        risks+=("suid_sgid_excessive")
        echo -e "${YELLOW}⚠️ Muitos arquivos SUID/SGID${NC}"
    fi
    
    # Firewall status
    if ! command -v ufw >/dev/null && ! command -v firewall-cmd >/dev/null && ! command -v iptables >/dev/null; then
        risks+=("no_firewall")
        echo -e "${RED}❌ Nenhum firewall detectado${NC}"
    fi
    
    # SSH Root login
    if [ -f /etc/ssh/sshd_config ] && ! grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then
        risks+=("ssh_root_login")
        echo -e "${RED}❌ SSH Root login habilitado${NC}"
    fi
    
    # Score (0-100)
    local score=$((100 - ${#risks[@]} * 10))
    [ $score -lt 0 ] && score=0
    jq ".scan.score = $score | .scan.risks = $(printf '%s
' "${risks[@]}" | jq -R . | jq -s .)" "$LOG_FILE" > tmp && mv tmp "$LOG_FILE"
    
    echo -e "${GREEN}Security Score: $score/100${NC}"
}

# MAIN EXECUTION
main() {
    echo -e "${GREEN}🚀 Linux Vulnerability Master Scanner v2.0${NC}"
    echo "Distro: $(detect_distro)"
    echo "----------------------------------------"
    
    init_report
    check_security_updates
    scan_cves
    check_hardening
    
    echo -e "
${GREEN}✅ Scan completo! Relatório: $LOG_FILE${NC}"
    echo "cat $LOG_FILE"
}

# Run
main "$@"
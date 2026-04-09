#!/bin/bash
# =============================================================================
# Linux Vulnerability Master Scanner v2.1
# Suporte: Debian/Ubuntu/RHEL/CentOS/Fedora/SUSE/Alpine/Arch/Mint/Amazon
# =============================================================================

set -euo pipefail

# Cores e logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_FILE="vuln-master-$(date +%Y%m%d-%H%M).json"
TRIVY_OUTPUT="trivy-scan-$(date +%s).json"
HOSTNAME=$(hostname -f 2>/dev/null || hostname)
TIMESTAMP=$(date -Iseconds)

# Cleanup on exit
cleanup() {
    rm -f "$TRIVY_OUTPUT" tmp 2>/dev/null || true
}
trap cleanup EXIT

# Função: Detecta distro e gerenciador
detect_distro() {
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        echo "${ID}${VERSION_ID:-}" | tr '[:upper:]' '[:lower:]' | tr -d '"'
    elif [ -f /etc/redhat-release ]; then
        awk '{print tolower($1)}' /etc/redhat-release
    else
        echo "unknown"
    fi
}

# Função: Header JSON
init_report() {
    local distro
    distro=$(detect_distro)
    cat > "$LOG_FILE" << EOF
{
  "scan": {
    "host": "$HOSTNAME",
    "timestamp": "$TIMESTAMP",
    "distro": "$distro",
    "cves": {
      "critical": 0,
      "high": 0
    },
    "security_updates": 0,
    "risks": [],
    "score": 100
  }
}
EOF
}

# Função: Security Updates por distro
check_security_updates() {
    local distro
    distro=$(detect_distro)
    local count=0
    
    case "$distro" in
        ubuntu*|debian*|linuxmint*)
            if sudo apt update -qq 2>/dev/null; then
                count=$(apt list --upgradable 2>/dev/null | grep -i 'security' | wc -l | tr -d ' '); count=${count:-0}; [[ ! "$count" =~ ^[0-9]+$ ]] && count=0
            fi
            echo -e "Security updates (APT): ${YELLOW}$count${NC}"
            ;;
        fedora*)
            count=$(sudo dnf check-update --security 2>/dev/null | grep -cv '^$' || echo 0)
            echo -e "Security updates (DNF): ${YELLOW}$count${NC}"
            ;;
        rhel*|centos*|ol*|rocky*|almalinux*)
            if command -v dnf >/dev/null 2>&1; then
                count=$(sudo dnf updateinfo list security 2>/dev/null | grep -c ': ' || echo 0)
            else
                count=$(sudo yum check-update --security 2>/dev/null | wc -l || echo 0)
            fi
            echo -e "Security updates (YUM/DNF): ${YELLOW}$count${NC}"
            ;;
        suse*|opensuse*)
            count=$(sudo zypper lu -t security 2>/dev/null | grep -c '^S' || echo 0)
            echo -e "Security updates (Zypper): ${YELLOW}$count${NC}"
            ;;
        alpine*)
            if sudo apk update -q 2>/dev/null; then
                count=$(apk list --upgradable 2>/dev/null | wc -l || echo 0)
            fi
            echo -e "Security updates (APK): ${YELLOW}$count${NC}"
            ;;
        arch*|manjaro*)
            count=$(pacman -Qu 2>/dev/null | wc -l || echo 0)
            echo -e "Security updates (Pacman): ${YELLOW}$count${NC}"
            ;;
        amzn*|amazon*)
            count=$(sudo yum check-update --security 2>/dev/null | wc -l || echo 0)
            echo -e "Security updates (Amazon): ${YELLOW}$count${NC}"
            ;;
        *)
            echo -e "Security updates: ${YELLOW}N/A (distro não suportada)${NC}"
            ;;
    esac
    
    # Atualiza JSON com validação
    if command -v jq >/dev/null 2>&1; then
        local tmp_file
        tmp_file=$(mktemp)
        jq ".scan.security_updates = $count" "$LOG_FILE" > "$tmp_file" && mv "$tmp_file" "$LOG_FILE"
    fi
}

# Função: Instala Trivy universal
install_trivy() {
    if command -v trivy >/dev/null 2>&1; then
        return 0
    fi
    
    echo -e "${YELLOW}Instalando Trivy...${NC}"
    
    if command -v curl >/dev/null 2>&1; then
        if curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.50.0 >/dev/null 2>&1; then
            echo -e "${GREEN}Trivy instalado com sucesso${NC}"
            return 0
        fi
    fi
    
    # Fallback: tenta via snap
    if command -v snap >/dev/null 2>&1; then
        sudo snap install trivy >/dev/null 2>&1 && return 0
    fi
    
    echo -e "${RED}⚠️ Falha ao instalar Trivy. CVE scan será pulado.${NC}"
    return 1
}

# Função: Scan CVEs com Trivy
scan_cves() {
    if ! install_trivy; then
        jq '.scan.cves = {"critical": -1, "high": -1, "error": "Trivy não disponível"}' "$LOG_FILE" > tmp && mv tmp "$LOG_FILE"
        return 0
    fi
    
    echo -e "${YELLOW}=== Scanning CVEs (HIGH/CRITICAL) ===${NC}"
    
    if ! trivy fs / --severity HIGH,CRITICAL --format json --output "$TRIVY_OUTPUT" >/dev/null 2>&1; then
        echo -e "${RED}⚠️ Erro ao executar Trivy${NC}"
        jq '.scan.cves = {"critical": -1, "high": -1, "error": "Scan falhou"}' "$LOG_FILE" > tmp && mv tmp "$LOG_FILE"
        return 0
    fi
    
    local critical high
    critical=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' "$TRIVY_OUTPUT" 2>/dev/null || echo 0)
    high=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity=="HIGH")] | length' "$TRIVY_OUTPUT" 2>/dev/null || echo 0)
    
    local tmp_file
    tmp_file=$(mktemp)
    jq ".scan.cves = {\"critical\": $critical, \"high\": $high}" "$LOG_FILE" > "$tmp_file" && mv "$tmp_file" "$LOG_FILE"
    
    echo -e "CVEs ${RED}CRITICAL: $critical${NC} | ${YELLOW}HIGH: $high${NC}"
    
    # Mostra top 10 vulnerabilities
    echo ""
    trivy fs / --severity HIGH,CRITICAL --format table 2>/dev/null | head -15 || true
}

# Função: Hardening checks universais
check_hardening() {
    local risks=()
    local score=100
    
    # World writable files (exclui /proc, /sys, /dev)
    if find / -xdev -type f -perm -o+w 2>/dev/null | head -1 | grep -q .; then
        risks+=("world_writable_files")
        score=$((score - 15))
        echo -e "${RED}❌ World-writable files encontrados${NC}"
    fi
    
    # SUID/SGID excessivos (>50 arquivos)
    local suid_count
    suid_count=$(find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null | wc -l)
    if [ "$suid_count" -gt 50 ]; then
        risks+=("suid_sgid_excessive")
        score=$((score - 10))
        echo -e "${YELLOW}⚠️ Muitos arquivos SUID/SGID ($suid_count)${NC}"
    fi
    
    # Firewall status
    local has_firewall=false
    command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "active" && has_firewall=true
    command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state 2>/dev/null | grep -q "running" && has_firewall=true
    command -v iptables >/dev/null 2>&1 && iptables -L -n 2>/dev/null | grep -q "Chain" && has_firewall=true
    
    if [ "$has_firewall" = false ]; then
        risks+=("no_firewall")
        score=$((score - 20))
        echo -e "${RED}❌ Nenhum firewall ativo detectado${NC}"
    fi
    
    # SSH Root login
    if [ -f /etc/ssh/sshd_config ]; then
        if ! grep -qE "^PermitRootLogin\s+no" /etc/ssh/sshd_config 2>/dev/null; then
            risks+=("ssh_root_login")
            score=$((score - 15))
            echo -e "${RED}❌ SSH Root login pode estar habilitado${NC}"
        fi
    fi
    
    # Verifica se há mais de 100 usuários
    local user_count
    user_count=$(cut -d: -f3 /etc/passwd | grep -c "^[0-9]\{4,\}$" || echo 0)
    if [ "$user_count" -gt 100 ]; then
        risks+=("excessive_users")
        score=$((score - 5))
        echo -e "${YELLOW}⚠️ Muitos usuários no sistema ($user_count)${NC}"
    fi
    
    # Garante score mínimo de 0
    [ "$score" -lt 0 ] && score=0
    
    # Converte array para JSON corretamente
    local risks_json="[]"
    if [ ${#risks[@]} -gt 0 ]; then
        risks_json=$(printf '%s\n' "${risks[@]}" | jq -R . | jq -s .)
    fi
    
    local tmp_file
    tmp_file=$(mktemp)
    jq ".scan.score = $score | .scan.risks = $risks_json" "$LOG_FILE" > "$tmp_file" && mv "$tmp_file" "$LOG_FILE"
    
    echo -e "${GREEN}✅ Security Score: $score/100${NC}"
}

# MAIN EXECUTION
main() {
    echo -e "${GREEN}🚀 Linux Vulnerability Master Scanner v2.1${NC}"
    echo "Host: $HOSTNAME"
    echo "Distro: $(detect_distro)"
    echo "Timestamp: $TIMESTAMP"
    echo "----------------------------------------"
    
    # Verifica dependências
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${RED}❌ Erro: jq não encontrado. Instale com: sudo apt install jq${NC}"
        exit 1
    fi
    
    init_report
    check_security_updates
    scan_cves
    check_hardening
    
    echo "----------------------------------------"
    echo -e "${GREEN}✅ Scan completo! Relatório: $LOG_FILE${NC}"
    echo ""
    echo "📊 Resumo:"
    jq '.scan | {host, distro, score, security_updates, cves, risks}' "$LOG_FILE"
}

# Run
main "$@"

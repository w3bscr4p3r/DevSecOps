# 🚨 ATENÇÃO: The Gentlemen Ransomware – A Nova Ameaça Global que Atacou o Brasil

**Por Daniel Alves | Cyber Security Analyst**

Você já ouviu falar de um grupo de ransomware que surgiu do nada em 2025 e, em poucos meses, já comprometeu 47+ organizações em 17 países? Pois é, **The Gentlemen** não é brincadeira. E o pior: eles acabaram de atacar a **UniFil no Brasil** em fevereiro de 2026.

## De Onde Vieram Esses "Cavalheiros"?

Identificados em **julho de 2025**, The Gentlemen demonstram **sofisticação cirúrgica** desde o primeiro dia. Seu primeiro ataque documentado foi contra a **JN Aceros (Peru)** em junho. Desde então:

- **47+ vítimas publicadas** em seu leak site na dark web
- Setores visados: **manufatura, construção, saúde, seguros**
- **Presença global**: EUA, Europa, América Latina (incluindo 🇧🇷)
- **OPSEC de elite**: quase zero vazamentos de inteligência prévia

## TTPs que Assustam Qualquer SOC

```
Recon → Lateral → Persistência → Double Extortion
```

**Fase 1: Reconnaissance Profundo**
```
Advanced IP Scanner + Nmap + Enumeração AD massiva
> 60 grupos administrativos mapeados
```

**Fase 2: Abuso de Infra Legítima**
```
✅ Drivers assinados para bypass AV
✅ GPO abusado via NETLOGON (domain-wide)
✅ WMI/PowerShell para propagação
```

**Fase 3: Persistência Implacável**
```
AnyDesk + WinSCP (exfiltração criptografada)
Registry hijacking + Auto-restart no boot
Comprometimento de Domain Admins
```

## O Ataque Brasileiro: UniFil (Fev/2026)

```
📍 Alvo: Universidade Filadélfia (UniFil)
📈 Impacto: Criptografia enterprise-wide
💰 Status: Dados vazados no leak site
```

**Por que universidades?** Infraestrutura crítica + dados sensíveis + baixa maturidade em cibersegurança.

## 🛡️ IOCs Críticos para Hunting

```
🔍 Hashes do ransomware (SHA256): [Trend Micro Workbench]
🔍 Scripts batch maliciosos: 1.bat, enum_ad.bat
🔍 GPOs comprometidos: {Domain}\sysvol\*
🔍 Ferramentas usadas: AdvancedIPScanner.exe, WinSCP.com
```

## Como se Proteger AGORA

### 🔴 **Prioridade Máxima**
```
1. Backups 3-2-1 IMUTÁVEIS (off-line)
2. Hunting Query AD: "Advanced IP Scanner" OR "enum_ad"
3. Blocklist: WinSCP.exe, AnyDesk.exe (exceto autorizado)
```

### 🟡 **Detecção MDR**
```
Sigma Rules: TheGentlemen Ransomware (SOC Prime)
Trend Vision One: TTP coverage completo
EDR Query: GPO modification + WMI lateral movement
```

### 🟢 **Threat Intel Feeds**
```
MISP + AlienVault OTX (já com The Gentlemen IOCs)
Integre no seu ThreatFusion OSINT ⚡
```

## A Verdade Incômoda

**The Gentlemen não é um grupo novato.** A velocidade de operação, qualidade do OPSEC e TTPs enterprise-grade sugerem:

1. **Rebranding** de grupo estabelecido
2. **Funding pesado** (state-sponsored?)
3. **Acessos zero-day** via RaaS marketplace

## Call-to-Action 🚀

```
👉 SIEM hunting HOJE com as IOCs acima
👉 Teste seu ambiente: simule GPO abuse
👉 **ThreatFusion OSINT** pronto para monitorar The Gentlemen
```

#Ransomware #TheGentlemen #ThreatIntelligence #Ciberseguranca #OSINT #UniFil #ThreatFusion

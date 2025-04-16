import socket
from impacket.smbconnection import SMBConnection
import argparse

def check_smb_version(target_ip):
    try:
        # Tenta detectar a versão do SMB
        smb = SMBConnection(target_ip, target_ip, sess_port=445)
        smb.login('', '')  # Conexão anônima (apenas para detecção)
        
        dialect = smb.getDialect()
        versions = {
            0x0202: "SMBv1",
            0x0210: "SMBv2",
            0x0300: "SMBv3",
            0x0311: "SMBv3.1.1"
        }
        
        print(f"\n[+] Versão SMB detectada: {versions.get(dialect, 'Desconhecida')}")
        
        # Verifica vulnerabilidades conhecidas
        if dialect <= 0x0202:
            print(f"\033[91m[!] ALERTA: SMBv1 detectado - Extremamente vulnerável (CVE-2017-0144 EternalBlue)\033[0m")
        if dialect == 0x0210:
            print(f"\033[93m[!] AVISO: SMBv2 detectado - Recomendado atualizar para SMBv3 com criptografia\033[0m")
            
        smb.logoff()
        
    except Exception as e:
        print(f"\033[91m[!] Erro ao conectar via SMB: {str(e)}\033[0m")

def check_port_445(target_ip):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((target_ip, 445))
        
        if result == 0:
            print(f"\n[+] Porta 445 aberta - Serviço SMB em execução")
            return True
        else:
            print(f"\n[!] Porta 445 fechada - Serviço SMB não detectado")
            return False
            
    except Exception as e:
        print(f"\033[91m[!] Erro ao verificar porta 445: {str(e)}\033[0m")
        return False

def main():
    parser = argparse.ArgumentParser(description="Verificador de Segurança SMB")
    parser.add_argument("target", help="Endereço IP ou hostname do alvo")
    args = parser.parse_args()

    print(f"\n=== Verificando {args.target} ===")
    
    if check_port_445(args.target):
        check_smb_version(args.target)
    
    print("\n=== Recomendações de Segurança ===")
    print("- Desabilite SMBv1 imediatamente (via PowerShell: Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol)")
    print("- Atualize para SMBv3 com criptografia habilitada")
    print("- Restrinja acesso à porta 445 via firewall")
    print("- Implemente autenticação multifatorial para acesso a compartilhamentos")

if __name__ == "__main__":
    main()

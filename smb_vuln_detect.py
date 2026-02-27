import argparse
import json
import socket
import sys

from impacket import smb, smb3structs
from impacket.smbconnection import SMBConnection

EXIT_OK = 0
EXIT_PORT_CLOSED = 1
EXIT_SMB_ERROR = 2


def _dialect_name(dialect):
    """Retorna nome amigável para o dialeto negociado."""
    mapping = {
        smb.SMB_DIALECT: "SMBv1",
        smb3structs.SMB2_DIALECT_002: "SMB 2.0.2",
        smb3structs.SMB2_DIALECT_21: "SMB 2.1",
        smb3structs.SMB2_DIALECT_30: "SMB 3.0",
        smb3structs.SMB2_DIALECT_302: "SMB 3.0.2",
        smb3structs.SMB2_DIALECT_311: "SMB 3.1.1",
    }
    return mapping.get(dialect, f"Desconhecida ({dialect!r})")


def _risk_messages(dialect):
    """Classifica risco sem depender de comparação numérica frágil."""
    if dialect == smb.SMB_DIALECT:
        return [
            "\033[91m[!] ALERTA: SMBv1 detectado - Extremamente vulnerável (ex.: CVE-2017-0144 / EternalBlue)\033[0m"
        ]

    if dialect in (smb3structs.SMB2_DIALECT_002, smb3structs.SMB2_DIALECT_21):
        return [
            "\033[93m[!] AVISO: SMBv2 detectado - Recomenda-se SMBv3 com criptografia habilitada\033[0m"
        ]

    if dialect in (
        smb3structs.SMB2_DIALECT_30,
        smb3structs.SMB2_DIALECT_302,
        smb3structs.SMB2_DIALECT_311,
    ):
        return ["[+] SMBv3 detectado - mantenha patches e hardening atualizados"]

    return ["[!] Não foi possível classificar risco com confiança para o dialeto detectado"]


def check_port_445(target, timeout=3):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((target, 445))

        if result == 0:
            return True, "[+] Porta 445 aberta - Serviço SMB em execução"
        return False, "[!] Porta 445 fechada - Serviço SMB não detectado"
    except socket.gaierror as exc:
        return False, f"[!] Erro de resolução DNS/hostname: {exc}"
    except socket.timeout:
        return False, "[!] Timeout ao verificar porta 445"
    except OSError as exc:
        return False, f"[!] Erro de rede ao verificar porta 445: {exc}"


def check_smb_version(target, timeout=5, verbose=False):
    result = {
        "target": target,
        "dialect": None,
        "dialect_name": None,
        "anonymous_login": None,
        "messages": [],
        "error": None,
    }

    smb_conn = None
    try:
        smb_conn = SMBConnection(target, target, sess_port=445, timeout=timeout)
        dialect = smb_conn.getDialect()
        result["dialect"] = repr(dialect)
        result["dialect_name"] = _dialect_name(dialect)

        # Tentativa de login anônimo é opcional: se falhar, seguimos com a detecção.
        try:
            smb_conn.login("", "")
            result["anonymous_login"] = True
        except Exception as exc:
            result["anonymous_login"] = False
            if verbose:
                result["messages"].append(
                    f"[i] Login anônimo não permitido neste host: {exc}"
                )

        result["messages"].append(f"[+] Versão SMB detectada: {result['dialect_name']}")
        result["messages"].extend(_risk_messages(dialect))
        return result, EXIT_OK

    except socket.timeout:
        result["error"] = "Timeout na conexão SMB"
        return result, EXIT_SMB_ERROR
    except socket.gaierror as exc:
        result["error"] = f"Erro de resolução DNS/hostname: {exc}"
        return result, EXIT_SMB_ERROR
    except OSError as exc:
        result["error"] = f"Erro de rede SMB: {exc}"
        return result, EXIT_SMB_ERROR
    except Exception as exc:
        result["error"] = f"Falha na negociação SMB: {exc}"
        return result, EXIT_SMB_ERROR
    finally:
        if smb_conn is not None:
            try:
                smb_conn.logoff()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="Verificador de Segurança SMB")
    parser.add_argument("target", help="Endereço IP ou hostname do alvo")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout em segundos")
    parser.add_argument("--json", action="store_true", help="Saída estruturada em JSON")
    parser.add_argument("--verbose", action="store_true", help="Mostra detalhes adicionais")
    args = parser.parse_args()

    if not args.json:
        print(f"\n=== Verificando {args.target} ===")

    port_open, port_message = check_port_445(args.target, timeout=args.timeout)
    output = {
        "target": args.target,
        "port_445_open": port_open,
        "port_445_message": port_message,
        "smb": None,
        "recommendations": [
            "Desabilite SMBv1 imediatamente",
            "Atualize para SMBv3 com criptografia habilitada",
            "Restrinja acesso à porta 445 via firewall",
            "Implemente autenticação multifatorial para acesso a compartilhamentos",
        ],
    }

    if not port_open:
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"\n{port_message}")
        return EXIT_PORT_CLOSED

    smb_result, code = check_smb_version(args.target, timeout=args.timeout, verbose=args.verbose)
    output["smb"] = smb_result

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"\n{port_message}")
        if smb_result["error"]:
            print(f"\033[91m[!] Erro ao conectar via SMB: {smb_result['error']}\033[0m")
        for message in smb_result["messages"]:
            print(message)

        print("\n=== Recomendações de Segurança ===")
        for recommendation in output["recommendations"]:
            print(f"- {recommendation}")

    return code


if __name__ == "__main__":
    sys.exit(main())

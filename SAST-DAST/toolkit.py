import os
import argparse
import subprocess
import requests
from bs4 import BeautifulSoup
import json
import yaml

# Configurações
CONFIG_FILE = "config.yaml"
PAYLOADS_FILE = "payloads.txt"

# ========== SAST ========== #
class SASTScanner:
    def __init__(self, path):
        self.path = path

    def run_bandit(self):
        """Executa Bandit para análise estática de código Python."""
        try:
            result = subprocess.run(
                ["bandit", "-r", self.path, "-f", "json"],
                capture_output=True,
                text=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Erro no Bandit: {e}")
            return {}

    def check_dependencies(self):
        """Verifica dependências vulneráveis usando safety."""
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Erro no safety: {e}")
            return {}

# ========== DAST ========== #
class DASTScanner:
    def __init__(self, target_url):
        self.target_url = target_url
        self.payloads = self._load_payloads()

    def _load_payloads(self):
        """Carrega payloads de um arquivo externo."""
        if os.path.exists(PAYLOADS_FILE):
            with open(PAYLOADS_FILE, "r") as f:
                return [line.strip() for line in f.readlines()]
        return []

    def test_sqli(self, params):
        """Testa vulnerabilidades de SQL Injection."""
        for payload in self.payloads:
            modified_params = {k: payload for k in params}
            response = requests.get(self.target_url, params=modified_params)
            if "error in your SQL syntax" in response.text:
                return True, payload
        return False, None

    def check_headers(self):
        """Verifica headers de segurança."""
        response = requests.get(self.target_url)
        headers = response.headers
        issues = []
        if 'Content-Security-Policy' not in headers:
            issues.append("CSP ausente")
        if 'X-Content-Type-Options' not in headers:
            issues.append("X-Content-Type-Options ausente")
        return issues

# ========== CLI ========== #
def main():
    parser = argparse.ArgumentParser(description="SAST/DAST Toolkit")
    parser.add_argument("--sast", help="Caminho do código para análise SAST")
    parser.add_argument("--dast", help="URL para análise DAST")
    args = parser.parse_args()

    if args.sast:
        sast = SASTScanner(args.sast)
        bandit_results = sast.run_bandit()
        print("[SAST] Resultados do Bandit:", json.dumps(bandit_results, indent=2))
        
    if args.dast:
        dast = DASTScanner(args.dast)
        headers_issues = dast.check_headers()
        print("[DAST] Problemas em headers:", headers_issues)

if __name__ == "__main__":
    main()

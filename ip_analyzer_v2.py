# osint_tool_gui.py

# --- Imports ---
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import json
import socket
import re
from datetime import datetime
import requests
import shodan # Certifique-se de ter 'shodan' instalado: pip install shodan
import time

# --- Configurações de API e Banco de Dados (localizadas neste arquivo) ---
# IMPORTANTE: Mantenha suas chaves de API seguras e nunca as compartilhe publicamente.
# Substitua "YOUR_API_KEY" pelas suas chaves reais.
ABUSEIPDB_API_KEY = "YOUR_API_KEY"
SHODAN_API_KEY = "YOUR_API_KEY"
VIRUSTOTAL_API_KEY = "YOUR_API_KEY"

# Nome do arquivo do banco de dados SQLite
DATABASE_FILE = "osint_results.db"

# --- Funções do Banco de Dados ---
def connect_db():
    """Estabelece uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

import sqlite3 # Importa sqlite3 aqui para as funções de DB

def create_table():
    """Cria a tabela 'results' se ela não existir."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT NOT NULL,
            query_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            abuseipdb_data TEXT,
            shodan_data TEXT,
            virustotal_data TEXT,
            google_dorks TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_results(target, query_type, results_data):
    """
    Salva os resultados OSINT no banco de dados.

    Args:
        target (str): O endereço IP ou domínio consultado.
        query_type (str): 'ip' ou 'domain'.
        results_data (dict): Um dicionário contendo todos os dados OSINT coletados.
    """
    conn = connect_db()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    abuseipdb_json = json.dumps(results_data.get('abuseipdb', {}), ensure_ascii=False)
    shodan_json = json.dumps(results_data.get('shodan', {}), ensure_ascii=False)
    virustotal_json = json.dumps(results_data.get('virustotal', {}), ensure_ascii=False)
    google_dorks_json = json.dumps(results_data.get('google_dorks', []), ensure_ascii=False) # Armazena como array JSON

    cursor.execute('''
        INSERT INTO results (target, query_type, timestamp, abuseipdb_data, shodan_data, virustotal_data, google_dorks)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (target, query_type, timestamp, abuseipdb_json, shodan_json, virustotal_json, google_dorks_json))
    
    conn.commit()
    conn.close()
    print(f"Resultados para {target} salvos no banco de dados.")


# --- Funções de Consulta de API ---

def query_abuseipdb(ip_address):
    """
    Consulta AbuseIPDB para obter informações sobre um endereço IP.

    Args:
        ip_address (str): O endereço IP a ser consultado.

    Returns:
        dict: Dados do AbuseIPDB ou uma mensagem de erro.
    """
    if not ABUSEIPDB_API_KEY or ABUSEIPDB_API_KEY == "YOUR_ABUSEIPDB_API_KEY":
        return {"error": "Chave da API AbuseIPDB não configurada."}

    url = f"https://api.abuseipdb.com/api/v2/check"
    headers = {
        "Key": ABUSEIPDB_API_KEY,
        "Accept": "application/json"
    }
    params = {
        "ipAddress": ip_address,
        "maxAgeInDays": 90, # Quão longe no passado para verificar relatórios
        "verbose": True
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # Levanta uma exceção para erros HTTP
        return response.json().get('data', {})
    except requests.exceptions.HTTPError as errh:
        return {"error": f"Erro HTTP: {errh}", "status_code": response.status_code, "response": response.text}
    except requests.exceptions.ConnectionError as errc:
        return {"error": f"Erro de Conexão: {errc}"}
    except requests.exceptions.Timeout as errt:
        return {"error": f"Erro de Timeout: {errt}"}
    except requests.exceptions.RequestException as err:
        return {"error": f"Algo inesperado aconteceu: {err}"}

def query_shodan(target, query_type):
    """
    Consulta Shodan para obter informações sobre um endereço IP ou domínio.

    Args:
        target (str): O endereço IP ou domínio a ser consultado.
        query_type (str): 'ip' ou 'domain'.

    Returns:
        dict: Dados do Shodan ou uma mensagem de erro.
    """
    if not SHODAN_API_KEY or SHODAN_API_KEY == "YOUR_SHODAN_API_KEY":
        return {"error": "Chave da API Shodan não configurada."}

    try:
        api = shodan.Shodan(SHODAN_API_KEY)

        if query_type == 'ip':
            # Busca informações do IP
            results = api.host(target)
            return results
        elif query_type == 'domain':
            # Resolve o domínio para IP primeiro, depois pesquisa
            try:
                ip_address = socket.gethostbyname(target)
                domain_info = api.dns.domain_info(target) # Obter informações específicas do domínio se disponíveis
                host_info = api.host(ip_address) # Obter informações do host para o IP resolvido
                return {"resolved_ip": ip_address, "domain_info": domain_info, "host_info": host_info}
            except socket.gaierror:
                return {"error": f"Não foi possível resolver o domínio {target} para um endereço IP."}
            except shodan.exception.APIError as e:
                 # É possível que a informação do domínio exista, mas o IP não tenha uma entrada
                if "No information available for that domain" in str(e):
                    try:
                        ip_address = socket.gethostbyname(target)
                        host_info = api.host(ip_address)
                        return {"resolved_ip": ip_address, "domain_info": {"error": "Nenhuma informação específica de domínio do Shodan"}, "host_info": host_info}
                    except socket.gaierror:
                        return {"error": f"Não foi possível resolver o domínio {target} para um endereço IP."}
                    except shodan.exception.APIError as e:
                        return {"error": f"Erro da API Shodan para o IP resolvido {ip_address}: {e}"}
                return {"error": f"Erro da API Shodan para o domínio {target}: {e}"}

    except shodan.exception.APIError as e:
        return {"error": f"Erro da API Shodan: {e}"}
    except Exception as e:
        return {"error": f"Ocorreu um erro inesperado com Shodan: {e}"}

def query_virustotal(target, query_type):
    """
    Consulta VirusTotal para obter informações sobre um endereço IP ou domínio.
    Nota: A API pública tem limites de taxa rigorosos (4 requisições/minuto).

    Args:
        target (str): O endereço IP ou domínio a ser consultado.
        query_type (str): 'ip' ou 'domain'.

    Returns:
        dict: Dados do VirusTotal ou uma mensagem de erro.
    """
    if not VIRUSTOTAL_API_KEY or VIRUSTOTAL_API_KEY == "YOUR_VIRUSTOTAL_API_KEY":
        return {"error": "Chave da API VirusTotal não configurada."}

    base_url = "https://www.virustotal.com/api/v3/"
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY,
        "Accept": "application/json"
    }

    endpoint = ""
    if query_type == 'ip':
        endpoint = f"ip_addresses/{target}"
    elif query_type == 'domain':
        endpoint = f"domains/{target}"
    else:
        return {"error": "Tipo de consulta inválido para VirusTotal. Deve ser 'ip' ou 'domain'."}

    url = base_url + endpoint
    
    # Introduz um pequeno atraso para mitigar limites de taxa da API pública (4 requisições/minuto)
    time.sleep(15) 

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Levanta uma exceção para erros HTTP
        return response.json().get('data', {})
    except requests.exceptions.HTTPError as errh:
        if response.status_code == 429:
            return {"error": f"Limite de Requisições do VirusTotal Excedido: {errh}. Por favor, aguarde e tente novamente.", "status_code": response.status_code, "response": response.text}
        return {"error": f"Erro HTTP: {errh}", "status_code": response.status_code, "response": response.text}
    except requests.exceptions.ConnectionError as errc:
        return {"error": f"Erro de Conexão: {errc}"}
    except requests.exceptions.Timeout as errt:
        return {"error": f"Erro de Timeout: {errt}"}
    except requests.exceptions.RequestException as err:
        return {"error": f"Algo inesperado aconteceu: {err}"}

def generate_google_dorks(target, query_type):
    """
    Gera uma lista de Google Dorks comuns para um determinado alvo.
    
    Args:
        target (str): O endereço IP ou domínio para gerar as dorks.
        query_type (str): 'ip' ou 'domain'.

    Returns:
        list: Uma lista de strings de Google Dorks.
    """
    dorks = []
    
    if query_type == 'domain':
        # Dorks gerais para domínios
        dorks.append(f"site:{target}")
        dorks.append(f"site:{target} intitle:login")
        dorks.append(f"site:{target} inurl:admin")
        dorks.append(f"site:{target} filetype:pdf")
        dorks.append(f"site:{target} filetype:doc | filetype:docx")
        dorks.append(f"site:{target} intitle:index.of")
        dorks.append(f"site:{target} inurl:.git")
        dorks.append(f"site:{target} intext:password")
        dorks.append(f"site:{target} related:") # Útil para encontrar sites semelhantes, requer entrada manual no navegador
        dorks.append(f"inurl:/{target}/") # Procurar por listagens de diretórios relacionadas ao domínio
        dorks.append(f"site:pastebin.com {target}") # Verificar pastebin por menções
        dorks.append(f"\"Powered by\" site:{target}") # Verificar informações de CMS/Framework

        # Se for um domínio, pesquisá-lo como uma frase em geral
        dorks.append(f"\"{target}\"")
        dorks.append(f"\"{target}\" email | contact | support")

    elif query_type == 'ip':
        # Dorks específicas para endereços IP (menos comuns para pesquisa direta, mas possíveis)
        # Nota: O Google frequentemente remove pesquisas diretas de IP dos resultados para evitar abuso.
        dorks.append(f"\"{target}\"") # Pesquisar a string exata do IP
        dorks.append(f"inurl:{target}") # Procurar o IP em URLs
        dorks.append(f"intitle:{target}") # Procurar o IP em títulos
        dorks.append(f"site:pastebin.com {target}") # Verificar pastebin por menções do IP
        dorks.append(f"\"index of /\" {target}") # Listagens de diretórios nesse IP
        dorks.append(f"intext:\"Server at {target} Port 80\"") # Páginas padrão do Apache

    # Adicionar algumas dorks gerais que podem se aplicar a ambos
    dorks.append(f"\"Powered by\" {target}")
    dorks.append(f"intext:\"version\" {target}")
    dorks.append(f"intitle:\"admin console\" {target}")

    return dorks

# --- Classe da Aplicação GUI (OSINTApp) ---
class OSINTApp:
    def __init__(self, master):
        self.master = master
        master.title("Ferramenta OSINT (PT-BR)")
        master.geometry("850x650") # Tamanho da janela
        master.resizable(False, False) # Impede que a janela seja redimensionada

        # Configuração de estilo (opcional, para uma aparência mais moderna)
        master.tk_setPalette(background='#ececec', foreground='#333333',
                             activeBackground='#c3c3c3', activeForeground='#000000')

        # Frame principal para organização
        main_frame = tk.Frame(master, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Rótulo e Campo de Entrada para o Alvo
        self.label_target = tk.Label(main_frame, text="Alvo (IP ou Domínio):", font=('Arial', 10, 'bold'))
        self.label_target.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.entry_target = tk.Entry(main_frame, width=60, font=('Arial', 10), bd=2, relief=tk.GROOVE)
        self.entry_target.grid(row=0, column=1, padx=(5, 0), pady=(0, 5), sticky=tk.EW)
        
        # Botões
        self.button_search = tk.Button(main_frame, text="Pesquisar", command=self.start_osint_query,
                                       font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white', relief=tk.RAISED)
        self.button_search.grid(row=0, column=2, padx=(10, 0), pady=(0, 5), sticky=tk.E)

        self.button_clear = tk.Button(main_frame, text="Limpar Resultados", command=self.clear_results,
                                      font=('Arial', 10), bg='#f44336', fg='white', relief=tk.RAISED)
        self.button_clear.grid(row=1, column=2, padx=(10, 0), pady=(0, 5), sticky=tk.E)

        # Rótulo de Status
        self.status_label = tk.Label(main_frame, text="Pronto.", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                     font=('Arial', 9))
        self.status_label.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=(5, 10))

        # Área de Texto para Resultados com Scroll
        self.results_label = tk.Label(main_frame, text="Resultados:", font=('Arial', 10, 'bold'))
        self.results_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 5))

        self.results_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=95, height=28,
                                                      font=('Consolas', 9), bd=2, relief=tk.SUNKEN,
                                                      state='disabled', bg='#ffffff', fg='#000000')
        self.results_text.grid(row=4, column=0, columnspan=3, sticky=tk.NSEW)

        # Configurar expansão de colunas e linhas
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)

        # Inicializar o banco de dados
        create_table()
        self.update_status("Banco de dados inicializado e tabela 'results' verificada.")

    def is_valid_ip(self, target):
        """Verifica se o alvo é um endereço IPv4 válido."""
        try:
            socket.inet_aton(target)
            return True
        except socket.error:
            return False

    def is_valid_domain(self, target):
        """Verifica se o alvo parece um nome de domínio válido."""
        if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target):
            return True
        return False

    def start_osint_query(self):
        """Inicia a consulta OSINT em uma thread separada para não bloquear a GUI."""
        target = self.entry_target.get().strip()
        if not target:
            messagebox.showwarning("Entrada Inválida", "Por favor, insira um IP ou domínio para pesquisar.")
            return

        self.update_status("Iniciando pesquisa...")
        self.clear_results()
        self.results_text.config(state='normal')
        self.results_text.insert(tk.END, "Pesquisando...\n")
        self.results_text.config(state='disabled')
        
        self.button_search.config(state='disabled') # Desabilita o botão durante a pesquisa
        self.entry_target.config(state='disabled') # Desabilita o campo de entrada

        # Executa a consulta em uma thread separada
        self.query_thread = threading.Thread(target=self._run_osint_query, args=(target,))
        self.query_thread.start()

    def _run_osint_query(self, target):
        """Função para executar todas as consultas OSINT."""
        try:
            query_type = None
            if self.is_valid_ip(target):
                query_type = "ip"
                self.update_status(f"Alvo '{target}' identificado como endereço IP.")
            elif self.is_valid_domain(target):
                query_type = "domain"
                self.update_status(f"Alvo '{target}' identificado como nome de domínio.")
            else:
                messagebox.showerror("Entrada Inválida", f"Erro: '{target}' não é um endereço IP ou formato de domínio válido.")
                self.update_status("Pronto.")
                self.button_search.config(state='normal')
                self.entry_target.config(state='normal')
                return

            all_results = {
                "target": target,
                "query_type": query_type,
                "timestamp": datetime.now().isoformat(),
                "abuseipdb": {},
                "shodan": {},
                "virustotal": {},
                "google_dorks": []
            }

            self.update_status("\n--- Executando Consultas OSINT ---")

            # 1. AbuseIPDB (apenas para IPs)
            if query_type == "ip":
                self.update_status("Consultando AbuseIPDB...")
                abuseipdb_data = query_abuseipdb(target)
                all_results["abuseipdb"] = abuseipdb_data
                self.update_status("AbuseIPDB Concluído.")
            else:
                self.update_status("Ignorando AbuseIPDB (aplicável apenas a endereços IP).")

            # 2. Shodan
            self.update_status("Consultando Shodan...")
            shodan_data = query_shodan(target, query_type)
            all_results["shodan"] = shodan_data
            self.update_status("Shodan Concluído.")

            # 3. VirusTotal
            self.update_status("Consultando VirusTotal... (Pode demorar devido a limites de taxa da API pública)")
            virustotal_data = query_virustotal(target, query_type)
            all_results["virustotal"] = virustotal_data
            self.update_status("VirusTotal Concluído.")

            # 4. Google Dorks
            self.update_status("Gerando Google Dorks...")
            google_dorks = generate_google_dorks(target, query_type)
            all_results["google_dorks"] = google_dorks
            self.update_status("Google Dorks Gerados.")

            self.update_status("\n--- Análise OSINT Concluída ---")

            # Salvar resultados no banco de dados
            save_results(target, query_type, all_results)
            self.update_status(f"Resultados para {target} salvos no banco de dados.")

            # Exibir resultados em JSON na área de texto
            self.update_results(json.dumps(all_results, indent=4, ensure_ascii=False))
            self.update_status("Pronto.")

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante a pesquisa: {e}")
            self.update_status("Pronto (com erro).")
        finally:
            self.button_search.config(state='normal') # Reabilita o botão
            self.entry_target.config(state='normal') # Reabilita o campo de entrada

    def update_status(self, message):
        """Atualiza o rótulo de status de forma segura para threads."""
        self.master.after(0, lambda: self.status_label.config(text=message))

    def update_results(self, text):
        """Atualiza a área de texto de resultados de forma segura para threads."""
        self.master.after(0, lambda: self._do_update_results(text))

    def _do_update_results(self, text):
        """Função interna para atualizar a área de texto de resultados."""
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, text)
        self.results_text.config(state='disabled')

    def clear_results(self):
        """Limpa a área de texto de resultados e o status."""
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state='disabled')
        self.status_label.config(text="Resultados limpos. Pronto.")

# --- Ponto de Entrada Principal da Aplicação ---
if __name__ == "__main__":
    root = tk.Tk()
    app = OSINTApp(root)
    root.mainloop()


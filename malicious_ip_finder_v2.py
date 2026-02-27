import csv
import os

import PySimpleGUI as sg
import requests as rq
import shodan

API_ENDPOINT = 'https://api.abuseipdb.com/api/v2/check/'
ABUSEIPDB_KEY = os.getenv('ABUSEIPDB_KEY')
SHODAN_KEY = os.getenv('SHODAN_KEY')
REQUEST_TIMEOUT_SECONDS = 10
ABUSE_THRESHOLD = 30


def build_window():
    sg.theme('Dark Blue 3')
    layout = [
        [sg.Text('Origem: ')],
        [sg.Input(key='Origem'), sg.FileBrowse()],
        [sg.Text('Destino: ')],
        [sg.Input(key='Destino'), sg.FileBrowse()],
        [
            sg.Button('Pesquisar', key='Search'),
            sg.Button('Limpar', key='Clear'),
            sg.Button('Sair', key='Quit'),
        ],
    ]
    return sg.Window('Pesquisador de IPs maliciosos by Daniel M. Alves', layout)


def get_shodan_client():
    if not SHODAN_KEY:
        raise ValueError('Variável SHODAN_KEY não configurada no ambiente.')
    return shodan.Shodan(SHODAN_KEY)


def get_abuse_headers():
    if not ABUSEIPDB_KEY:
        raise ValueError('Variável ABUSEIPDB_KEY não configurada no ambiente.')
    return {
        'Accept': 'application/json',
        'Key': ABUSEIPDB_KEY,
    }


def read_targets(source_path):
    targets = []
    with open(source_path, 'r', newline='', encoding='utf-8') as source_file:
        reader = csv.reader(source_file, delimiter=';')
        next(reader, None)  # pular cabeçalho
        for row in reader:
            if row and row[0].strip():
                targets.append(row[0].strip())
    return targets


def evaluate_ip(target, shodan_api, abuse_headers):
    response = rq.get(
        API_ENDPOINT,
        headers=abuse_headers,
        params={'ipAddress': target},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    response_data = response.json().get('data', {})

    host = shodan_api.host(target)

    score = response_data.get('abuseConfidenceScore', 0)
    is_malicious = 'Sim' if score >= ABUSE_THRESHOLD else 'Não'

    hostnames = response_data.get('hostnames') or []
    hostname = hostnames[0] if hostnames else response_data.get('domain') or 'sem informação'

    ports = host.get('ports') or []
    ports_out = str(ports) if ports else 'sem informação'

    isp = response_data.get('isp') or 'sem informação'

    city = host.get('city') or 'sem informação'

    vulns = host.get('vulns') or []
    vulns_out = str(vulns) if vulns else 'sem informação'

    country = response_data.get('countryCode') or 'sem informação'

    return [is_malicious, target, hostname, ports_out, isp, city, country, vulns_out]


def analyze_ips(source_path, destination_path):
    shodan_api = get_shodan_client()
    abuse_headers = get_abuse_headers()
    targets = read_targets(source_path)

    with open(destination_path, 'w', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file, delimiter=';')
        writer.writerow(['Malicioso', 'IP', 'DNS', 'Open Ports', 'ISP', 'City', 'Country', 'Vulns'])

        for target in targets:
            try:
                row = evaluate_ip(target, shodan_api, abuse_headers)
            except (rq.RequestException, shodan.APIError, ValueError, KeyError, TypeError):
                row = [
                    'sem informação',
                    target,
                    'sem informação',
                    'sem informação',
                    'sem informação',
                    'sem informação',
                    'sem informação',
                    'sem informação',
                ]
            writer.writerow(row)


def main():
    window = build_window()

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

        if event == 'Clear':
            window['Origem'].update('')
            window['Destino'].update('')
            continue

        if event != 'Search':
            continue

        origem = values.get('Origem', '').strip()
        destino = values.get('Destino', '').strip()

        if not origem or not destino:
            sg.popup_error('Selecione os arquivos de origem e destino antes de pesquisar.')
            continue

        if not os.path.isfile(origem):
            sg.popup_error('Arquivo de origem inválido.')
            continue

        try:
            analyze_ips(origem, destino)
            sg.popup('IPs analisados com sucesso!!')
        except ValueError as error:
            sg.popup_error(str(error))
        except OSError as error:
            sg.popup_error(f'Erro ao processar arquivo: {error}')

    window.close()


if __name__ == '__main__':
    main()

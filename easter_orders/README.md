# Sistema de Pedidos de Ovos de Páscoa - Léia

Aplicação web full-stack para gestão sazonal de pedidos, com backend Flask + SQLite e frontend React.

## Funcionalidades

- Cadastro de clientes.
- Cadastro de pedidos com múltiplos itens (quantidade, tamanho, casca, recheio e preço unitário).
- Regra obrigatória de entrada mínima de **50%** do valor total.
- Fluxo de status passo a passo: `novo -> entrada_paga -> em_preparo -> pronto_retirada -> entregue -> finalizado`.
- Filtros por status e por item/tamanho.
- Relatórios agregados por tamanho/casca e totais financeiros.
- Exportação CSV de pedidos.
- Interface responsiva para desktop e mobile.

## Como executar

```bash
cd easter_orders/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Acesse em: `http://localhost:5000`

## Principais endpoints

- `GET/POST /api/customers`
- `GET/POST /api/orders`
- `PATCH /api/orders/<id>/status`
- `GET /api/reports/totals`
- `GET /api/reports/orders.csv`

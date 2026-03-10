const { useEffect, useMemo, useState } = React;

const STATUSES = [
  "novo",
  "entrada_paga",
  "em_preparo",
  "pronto_retirada",
  "entregue",
  "finalizado",
];

function App() {
  const [customers, setCustomers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [totals, setTotals] = useState({ eggs_by_size: [], total_revenue: 0, total_down_payments: 0 });
  const [filter, setFilter] = useState({ status: "", size: "" });

  const [customerForm, setCustomerForm] = useState({ name: "", phone: "", email: "", notes: "" });
  const [orderForm, setOrderForm] = useState({
    customer_id: "",
    total_value: "",
    down_payment: "",
    delivery_forecast: "",
    notes: "",
    items: [{ quantity: 1, size: "250g", shell: "ao leite", filling: "brigadeiro", unit_price: 0 }],
  });

  const loadCustomers = async () => {
    const response = await fetch("/api/customers");
    setCustomers(await response.json());
  };

  const loadOrders = async () => {
    const params = new URLSearchParams();
    if (filter.status) params.append("status", filter.status);
    if (filter.size) params.append("size", filter.size);
    const response = await fetch(`/api/orders?${params.toString()}`);
    setOrders(await response.json());
  };

  const loadTotals = async () => {
    const response = await fetch("/api/reports/totals");
    setTotals(await response.json());
  };

  useEffect(() => {
    loadCustomers();
    loadOrders();
    loadTotals();
  }, []);

  useEffect(() => {
    loadOrders();
  }, [filter]);

  const createCustomer = async (event) => {
    event.preventDefault();
    const response = await fetch("/api/customers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(customerForm),
    });
    if (!response.ok) {
      alert("Erro ao cadastrar cliente");
      return;
    }
    setCustomerForm({ name: "", phone: "", email: "", notes: "" });
    await loadCustomers();
  };

  const createOrder = async (event) => {
    event.preventDefault();
    const response = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...orderForm, customer_id: Number(orderForm.customer_id) }),
    });
    if (!response.ok) {
      const error = await response.json();
      alert(error.error || "Erro ao criar pedido");
      return;
    }
    setOrderForm({
      customer_id: "",
      total_value: "",
      down_payment: "",
      delivery_forecast: "",
      notes: "",
      items: [{ quantity: 1, size: "250g", shell: "ao leite", filling: "brigadeiro", unit_price: 0 }],
    });
    await loadOrders();
    await loadTotals();
  };

  const nextStatus = useMemo(() => {
    const map = {};
    STATUSES.forEach((status, index) => {
      map[status] = STATUSES[index + 1] || status;
    });
    return map;
  }, []);

  const advanceStatus = async (order) => {
    const target = nextStatus[order.status];
    const response = await fetch(`/api/orders/${order.id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: target }),
    });
    if (response.ok) {
      await loadOrders();
    }
  };

  return (
    <div className="container">
      <h1>Gestão de Pedidos de Ovos da Léia</h1>
      <div className="grid">
        <section className="card">
          <h2>1) Cadastro de cliente</h2>
          <form onSubmit={createCustomer}>
            <input placeholder="Nome" value={customerForm.name} onChange={(e) => setCustomerForm({ ...customerForm, name: e.target.value })} required />
            <input placeholder="Telefone" value={customerForm.phone} onChange={(e) => setCustomerForm({ ...customerForm, phone: e.target.value })} required />
            <input placeholder="Email" value={customerForm.email} onChange={(e) => setCustomerForm({ ...customerForm, email: e.target.value })} />
            <textarea placeholder="Observações" value={customerForm.notes} onChange={(e) => setCustomerForm({ ...customerForm, notes: e.target.value })} />
            <button type="submit">Salvar cliente</button>
          </form>
        </section>

        <section className="card">
          <h2>2) Novo pedido (entrada mínima 50%)</h2>
          <form onSubmit={createOrder}>
            <select value={orderForm.customer_id} onChange={(e) => setOrderForm({ ...orderForm, customer_id: e.target.value })} required>
              <option value="">Selecione um cliente</option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>{customer.name} - {customer.phone}</option>
              ))}
            </select>
            {orderForm.items.map((item, index) => (
              <div key={index}>
                <input type="number" min="1" value={item.quantity} onChange={(e) => updateItem(index, "quantity", Number(e.target.value))} placeholder="Quantidade" />
                <input value={item.size} onChange={(e) => updateItem(index, "size", e.target.value)} placeholder="Tamanho" />
                <input value={item.shell} onChange={(e) => updateItem(index, "shell", e.target.value)} placeholder="Casca" />
                <input value={item.filling} onChange={(e) => updateItem(index, "filling", e.target.value)} placeholder="Recheio" />
                <input type="number" min="0" step="0.01" value={item.unit_price} onChange={(e) => updateItem(index, "unit_price", Number(e.target.value))} placeholder="Preço unitário" />
              </div>
            ))}
            <button type="button" className="secondary" onClick={() => setOrderForm({ ...orderForm, items: [...orderForm.items, { quantity: 1, size: "", shell: "", filling: "", unit_price: 0 }] })}>Adicionar item</button>
            <input type="number" step="0.01" value={orderForm.total_value} onChange={(e) => setOrderForm({ ...orderForm, total_value: e.target.value })} placeholder="Valor total" required />
            <input type="number" step="0.01" value={orderForm.down_payment} onChange={(e) => setOrderForm({ ...orderForm, down_payment: e.target.value })} placeholder="Entrada" required />
            <input type="date" value={orderForm.delivery_forecast} onChange={(e) => setOrderForm({ ...orderForm, delivery_forecast: e.target.value })} placeholder="Previsão de entrega" />
            <textarea placeholder="Observações do pedido" value={orderForm.notes} onChange={(e) => setOrderForm({ ...orderForm, notes: e.target.value })} />
            <button type="submit">Criar pedido</button>
          </form>
        </section>
      </div>

      <section className="card">
        <h2>Filtros e controle de status</h2>
        <div className="grid">
          <select value={filter.status} onChange={(e) => setFilter({ ...filter, status: e.target.value })}>
            <option value="">Todos os status</option>
            {STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
          <input placeholder="Filtrar por tamanho (ex: 350g)" value={filter.size} onChange={(e) => setFilter({ ...filter, size: e.target.value })} />
          <a href="/api/reports/orders.csv"><button>Exportar CSV</button></a>
        </div>
        {orders.map((order) => (
          <article key={order.id} className="card">
            <h3>Pedido #{order.id} - {order.customer.name}</h3>
            <p><span className="badge">{order.status}</span> | Total R$ {order.total_value.toFixed(2)} | Entrada R$ {order.down_payment.toFixed(2)}</p>
            <p>
              Data do pedido: <strong>{new Date(order.order_date || order.created_at).toLocaleString("pt-BR")}</strong>
              {" | "}
              Previsão de entrega: <strong>{order.delivery_forecast ? new Date(`${order.delivery_forecast}T00:00:00`).toLocaleDateString("pt-BR") : "Não informada"}</strong>
            </p>
            <ul>
              {order.items.map((item) => <li key={item.id}>{item.quantity}x {item.size} | {item.shell} | {item.filling}</li>)}
            </ul>
            {nextStatus[order.status] !== order.status && <button onClick={() => advanceStatus(order)}>Avançar para {nextStatus[order.status]}</button>}
          </article>
        ))}
      </section>

      <section className="card">
        <h2>Relatório resumido</h2>
        <p>Total de vendas: <strong>R$ {totals.total_revenue.toFixed(2)}</strong></p>
        <p>Total de entradas: <strong>R$ {totals.total_down_payments.toFixed(2)}</strong></p>
        <table>
          <thead><tr><th>Tamanho</th><th>Quantidade de ovos</th></tr></thead>
          <tbody>
            {totals.eggs_by_size.map((row) => <tr key={row.size}><td>{row.size}</td><td>{row.quantity}</td></tr>)}
          </tbody>
        </table>
      </section>
    </div>
  );

  function updateItem(index, key, value) {
    const updated = [...orderForm.items];
    updated[index] = { ...updated[index], [key]: value };
    setOrderForm({ ...orderForm, items: updated });
  }
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

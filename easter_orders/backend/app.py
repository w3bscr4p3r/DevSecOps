from __future__ import annotations

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

STATUSES = [
    "novo",
    "entrada_paga",
    "em_preparo",
    "pronto_retirada",
    "entregue",
    "finalizado",
]


db = SQLAlchemy()


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", back_populates="customer", cascade="all, delete-orphan")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    status = db.Column(db.String(30), default=STATUSES[0], nullable=False)
    total_value = db.Column(db.Numeric(10, 2), nullable=False)
    down_payment = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(30), nullable=False)
    shell = db.Column(db.String(80), nullable=False)
    filling = db.Column(db.String(120), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")


def create_app(database_uri: str | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or f"sqlite:///{BASE_DIR / 'easter_orders.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def root():
        return app.send_static_file("index.html")

    @app.get("/api/customers")
    def list_customers():
        search = request.args.get("search", "").strip()
        query = Customer.query
        if search:
            like = f"%{search}%"
            query = query.filter((Customer.name.ilike(like)) | (Customer.phone.ilike(like)))
        customers = query.order_by(Customer.created_at.desc()).all()
        return jsonify([serialize_customer(customer) for customer in customers])

    @app.post("/api/customers")
    def create_customer():
        data = request.get_json(force=True)
        customer = Customer(
            name=data.get("name", "").strip(),
            phone=data.get("phone", "").strip(),
            email=data.get("email", "").strip() or None,
            notes=data.get("notes", "").strip() or None,
        )
        if not customer.name or not customer.phone:
            return jsonify({"error": "Nome e telefone são obrigatórios."}), 400
        db.session.add(customer)
        db.session.commit()
        return jsonify(serialize_customer(customer)), 201

    @app.get("/api/orders")
    def list_orders():
        status = request.args.get("status")
        size = request.args.get("size")
        shell = request.args.get("shell")
        filling = request.args.get("filling")

        query = Order.query.join(Customer).options(db.joinedload(Order.items))
        if status:
            query = query.filter(Order.status == status)
        if size or shell or filling:
            query = query.join(Order.items)
            if size:
                query = query.filter(OrderItem.size == size)
            if shell:
                query = query.filter(OrderItem.shell == shell)
            if filling:
                query = query.filter(OrderItem.filling == filling)
        orders = query.order_by(Order.created_at.desc()).distinct().all()
        return jsonify([serialize_order(order) for order in orders])

    @app.post("/api/orders")
    def create_order():
        data = request.get_json(force=True)
        customer_id = data.get("customer_id")
        if not customer_id:
            return jsonify({"error": "customer_id é obrigatório."}), 400

        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({"error": "Cliente não encontrado."}), 404

        items_payload = data.get("items", [])
        if not items_payload:
            return jsonify({"error": "Pedido precisa ter ao menos 1 item."}), 400

        total_value = parse_money(data.get("total_value"))
        down_payment = parse_money(data.get("down_payment"))
        if total_value is None or down_payment is None:
            return jsonify({"error": "Valores monetários inválidos."}), 400
        required_down_payment = total_value * Decimal("0.50")
        if down_payment < required_down_payment:
            return jsonify({"error": "Entrada deve ser de no mínimo 50% do valor total."}), 400

        order = Order(
            customer_id=customer_id,
            total_value=total_value,
            down_payment=down_payment,
            due_date=parse_date(data.get("due_date")),
            notes=(data.get("notes") or "").strip() or None,
            status="entrada_paga" if down_payment >= required_down_payment else "novo",
        )

        for item in items_payload:
            quantity = int(item.get("quantity", 0))
            unit_price = parse_money(item.get("unit_price"))
            if quantity <= 0 or unit_price is None:
                return jsonify({"error": "Item inválido: quantidade e preço unitário são obrigatórios."}), 400
            order.items.append(
                OrderItem(
                    quantity=quantity,
                    size=str(item.get("size", "")).strip(),
                    shell=str(item.get("shell", "")).strip(),
                    filling=str(item.get("filling", "")).strip(),
                    unit_price=unit_price,
                )
            )

        db.session.add(order)
        db.session.commit()
        return jsonify(serialize_order(order)), 201

    @app.patch("/api/orders/<int:order_id>/status")
    def update_order_status(order_id: int):
        order = Order.query.get_or_404(order_id)
        data = request.get_json(force=True)
        new_status = data.get("status")

        if new_status not in STATUSES:
            return jsonify({"error": "Status inválido."}), 400

        current_index = STATUSES.index(order.status)
        target_index = STATUSES.index(new_status)
        if target_index != current_index + 1 and target_index != current_index:
            return jsonify({"error": "Status deve avançar passo a passo."}), 400

        order.status = new_status
        db.session.commit()
        return jsonify(serialize_order(order))

    @app.get("/api/reports/totals")
    def report_totals():
        by_size = (
            db.session.query(OrderItem.size, func.sum(OrderItem.quantity))
            .group_by(OrderItem.size)
            .order_by(OrderItem.size)
            .all()
        )
        by_shell = (
            db.session.query(OrderItem.shell, func.sum(OrderItem.quantity))
            .group_by(OrderItem.shell)
            .order_by(OrderItem.shell)
            .all()
        )
        revenue = db.session.query(func.sum(Order.total_value)).scalar() or Decimal("0")
        down_payments = db.session.query(func.sum(Order.down_payment)).scalar() or Decimal("0")

        return jsonify(
            {
                "eggs_by_size": [{"size": size, "quantity": int(quantity)} for size, quantity in by_size],
                "eggs_by_shell": [{"shell": shell, "quantity": int(quantity)} for shell, quantity in by_shell],
                "total_revenue": float(revenue),
                "total_down_payments": float(down_payments),
            }
        )

    @app.get("/api/reports/orders.csv")
    def export_orders_csv():
        rows = (
            db.session.query(Order, Customer, OrderItem)
            .join(Customer, Order.customer_id == Customer.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .order_by(Order.created_at.desc())
            .all()
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "order_id",
                "cliente",
                "telefone",
                "status",
                "valor_total",
                "entrada",
                "data_entrega",
                "quantidade",
                "tamanho",
                "casca",
                "recheio",
                "preco_unitario",
            ]
        )
        for order, customer, item in rows:
            writer.writerow(
                [
                    order.id,
                    customer.name,
                    customer.phone,
                    order.status,
                    float(order.total_value),
                    float(order.down_payment),
                    order.due_date.isoformat() if order.due_date else "",
                    item.quantity,
                    item.size,
                    item.shell,
                    item.filling,
                    float(item.unit_price),
                ]
            )

        content = io.BytesIO(output.getvalue().encode("utf-8"))
        return send_file(content, mimetype="text/csv", as_attachment=True, download_name="pedidos_leia.csv")

    return app


def serialize_customer(customer: Customer) -> dict:
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "email": customer.email,
        "notes": customer.notes,
        "created_at": customer.created_at.isoformat(),
    }


def serialize_order(order: Order) -> dict:
    return {
        "id": order.id,
        "customer": serialize_customer(order.customer),
        "status": order.status,
        "total_value": float(order.total_value),
        "down_payment": float(order.down_payment),
        "due_date": order.due_date.isoformat() if order.due_date else None,
        "notes": order.notes,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "id": item.id,
                "quantity": item.quantity,
                "size": item.size,
                "shell": item.shell,
                "filling": item.filling,
                "unit_price": float(item.unit_price),
            }
            for item in order.items
        ],
    }


def parse_money(value: object) -> Decimal | None:
    try:
        if value is None:
            return None
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def parse_date(value: object):
    if not value:
        return None
    return datetime.fromisoformat(str(value)).date()


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)

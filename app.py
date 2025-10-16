from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
db_uri = os.getenv("DATABASE_URL", "sqlite:///inventory.db")
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    location = db.Column(db.String(100), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "sku": self.sku, "name": self.name,
                "quantity": self.quantity, "location": self.location,
                "last_updated": self.last_updated.isoformat() if self.last_updated else None}

def init_db():
    with app.app_context():          # required for Flask-SQLAlchemy 3.x
        db.create_all()              # idempotent; safe if called more than once

init_db()

@app.route("/")
def index():
    items = Item.query.order_by(Item.name).all()
    return render_template("index.html", items=items)

# REST endpoints
@app.route("/api/items", methods=["GET","POST"])
def items_api():
    if request.method == "GET":
        return jsonify([i.to_dict() for i in Item.query.all()])
    data = request.get_json()
    item = Item(sku=data['sku'], name=data['name'], quantity=int(data.get('quantity',0)), location=data.get('location'))
    db.session.add(item); db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route("/api/items/<int:item_id>", methods=["GET","PUT","DELETE"])
def item_api(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == "GET":
        return jsonify(item.to_dict())
    if request.method == "DELETE":
        db.session.delete(item); db.session.commit()
        return "", 204
    data = request.get_json()
    item.sku = data.get('sku', item.sku)
    item.name = data.get('name', item.name)
    item.quantity = int(data.get('quantity', item.quantity))
    item.location = data.get('location', item.location)
    db.session.commit()
    return jsonify(item.to_dict())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

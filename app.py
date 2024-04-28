from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parskats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(20))
    category = db.Column(db.String(100))
    name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date = db.Column(db.Date)

@app.route('/', methods=['GET'])
def index():
    items = Item.query.order_by(Item.name).all()
    print(items)  # Add this line to print items to console for debugging
    return render_template('index.html', data=items)

@app.route('/pievienosana', methods=['POST', 'GET'])
def pievienosana():
    if request.method == 'POST':
        item_type = request.form['type']
        category = request.form['category']
        name = request.form['name']
        amount = request.form['amount']
        date = request.form['date']

        items = Item(name=name, item_type=item_type, category=category, amount=amount, date=date)
        try:
            db.session.add(items)
            db.session.commit()
            return redirect('/pievienosana')
        except:
            return 'Kļūda'
    else:
        return render_template('pievienosana.html')

if __name__ == "__main__":
        app.run(debug=True)
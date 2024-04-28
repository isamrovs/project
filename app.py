import random
from datetime import datetime, date, timedelta

from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy


from collections import defaultdict
import os


from calendar import monthrange


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
        item_type = request.form['item_type']
        category = request.form['category']
        name = request.form['name']
        amount = request.form['amount']
        date_str = request.form['date']  # Получаем дату как строку
        date = datetime.strptime(date_str, '%Y-%m-%d').date()  # Преобразуем строку в объект datetime.date

        items = Item(name=name, item_type=item_type, category=category, amount=amount, date=date)
        try:
            db.session.add(items)
            db.session.commit()
            return redirect('/pievienosana')
        except:
            return 'Kļūda'
    else:
        return render_template('pievienosana.html')


# Роут для страницы с финансовым отчетом
@app.route('/parskats')
def parskats():
    return render_template('parskats.html')

@app.route('/get_financial_data')
def get_financial_data():
    # Вычисляем общую сумму расходов и доходов за все время
    total_expenses = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'expense').scalar() or 0
    total_income = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'income').scalar() or 0

    # Вычисляем общий баланс (доходы - расходы за все время)
    total_balance = total_income - total_expenses

    # Строим категориальное распределение для расходов и доходов за текущий месяц
    current_date = date.today()
    first_day_of_month = current_date.replace(day=1)
    _, last_day = monthrange(current_date.year, current_date.month)
    last_day_of_month = current_date.replace(day=last_day)
    total_expenses_month = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'expense', Item.date.between(first_day_of_month, last_day_of_month)).scalar() or 0
    total_income_month = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'income', Item.date.between(first_day_of_month, last_day_of_month)).scalar() or 0

    # Формируем данные для диаграмм
    expenses_data = db.session.query(Item.category, db.func.sum(Item.amount)).filter(Item.item_type == 'expense', Item.date.between(first_day_of_month, last_day_of_month)).group_by(Item.category).all()
    income_data = db.session.query(Item.category, db.func.sum(Item.amount)).filter(Item.item_type == 'income', Item.date.between(first_day_of_month, last_day_of_month)).group_by(Item.category).all()

    expenses_categories = [data[0] for data in expenses_data]
    expenses_amounts = [data[1] for data in expenses_data]
    income_categories = [data[0] for data in income_data]
    income_amounts = [data[1] for data in income_data]

    expenses_colors = ['#' + ("%06x" % random.randint(0, 0xFFFFFF)) for _ in range(len(expenses_categories))]
    income_colors = ['#' + ("%06x" % random.randint(0, 0xFFFFFF)) for _ in range(len(income_categories))]

    data = {
        "total_balance": total_balance,
        "total_expenses": total_expenses_month,
        "total_income": total_income_month,
        "expenses_categories": expenses_categories,
        "expenses_amounts": expenses_amounts,
        "expenses_colors": expenses_colors,
        "income_categories": income_categories,
        "income_amounts": income_amounts,
        "income_colors": income_colors
    }

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
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

@app.route('/get_financial_data', methods=['POST', 'GET'])
def get_financial_data():
    if request.method == 'POST':
        start_date = request.json['start_date']
        end_date = request.json['end_date']
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Данные за выбранный период
        period_expenses = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'expense', Item.date.between(start_date, end_date)).scalar() or 0
        period_income = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'income', Item.date.between(start_date, end_date)).scalar() or 0

        period_expenses_data = db.session.query(Item.category, db.func.sum(Item.amount)).filter(Item.item_type == 'expense', Item.date.between(start_date, end_date)).group_by(Item.category).all()
        period_income_data = db.session.query(Item.category, db.func.sum(Item.amount)).filter(Item.item_type == 'income', Item.date.between(start_date, end_date)).group_by(Item.category).all()

        period_expenses_categories = [data[0] for data in period_expenses_data]
        period_expenses_amounts = [data[1] for data in period_expenses_data]
        period_income_categories = [data[0] for data in period_income_data]
        period_income_amounts = [data[1] for data in period_income_data]

        period_expenses_colors = ['#' + ("%06x" % random.randint(0, 0xFFFFFF)) for _ in range(len(period_expenses_categories))]
        period_income_colors = ['#' + ("%06x" % random.randint(0, 0xFFFFFF)) for _ in range(len(period_income_categories))]

        data = {
            "total_expenses_selected": period_expenses,
            "total_income_selected": period_income,
            "expenses_categories_selected": period_expenses_categories,
            "expenses_amounts_selected": period_expenses_amounts,
            "expenses_colors_selected": period_expenses_colors,
            "income_categories_selected": period_income_categories,
            "income_amounts_selected": period_income_amounts,
            "income_colors_selected": period_income_colors
        }

        return jsonify(data)
    else:
        # Данные за текущий месяц
        current_date = date.today()
        first_day_of_month = current_date.replace(day=1)
        _, last_day = monthrange(current_date.year, current_date.month)
        last_day_of_month = current_date.replace(day=last_day)

        total_expenses_month = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'expense', Item.date.between(first_day_of_month, last_day_of_month)).scalar() or 0
        total_income_month = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'income', Item.date.between(first_day_of_month, last_day_of_month)).scalar() or 0

        expenses_data_month = db.session.query(Item.category, db.func.sum(Item.amount)).filter(Item.item_type == 'expense', Item.date.between(first_day_of_month, last_day_of_month)).group_by(Item.category).all()
        income_data_month = db.session.query(Item.category, db.func.sum(Item.amount)).filter(Item.item_type == 'income', Item.date.between(first_day_of_month, last_day_of_month)).group_by(Item.category).all()

        expenses_categories_month = [data[0] for data in expenses_data_month]
        expenses_amounts_month = [data[1] for data in expenses_data_month]
        income_categories_month = [data[0] for data in income_data_month]
        income_amounts_month = [data[1] for data in income_data_month]

        expenses_colors_month = ['#' + ("%06x" % random.randint(0, 0xFFFFFF)) for _ in range(len(expenses_categories_month))]
        income_colors_month = ['#' + ("%06x" % random.randint(0, 0xFFFFFF)) for _ in range(len(income_categories_month))]

        # Общие данные
        total_expenses = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'expense').scalar() or 0
        total_income = db.session.query(db.func.sum(Item.amount)).filter(Item.item_type == 'income').scalar() or 0
        total_balance = total_income - total_expenses

        # Данные для передачи в HTML
        data = {
            "total_balance": total_balance,
            "total_expenses_month": total_expenses_month,
            "total_income_month": total_income_month,
            "expenses_categories_month": expenses_categories_month,
            "expenses_amounts_month": expenses_amounts_month,
            "expenses_colors_month": expenses_colors_month,
            "income_categories_month": income_categories_month,
            "income_amounts_month": income_amounts_month,
            "income_colors_month": income_colors_month
        }

        return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)

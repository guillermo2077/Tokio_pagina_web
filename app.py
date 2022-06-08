from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash
from jinja2 import *
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/tech_company.db'
app.config['SESSION_TYPE'] = 'filesystem'
db = SQLAlchemy(app)
app.secret_key = 'super secret key'


class Producto(db.Model):
    __tablename__ = "producto"

    idref = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    image_src = db.Column(db.String(200))

    description = db.Column(db.String(200))
    location = db.Column(db.String(200))
    opinions = db.Column(db.String(400))

    stock = db.Column(db.String(200))
    offer = db.Column(db.Float)
    price_retail = db.Column(db.Float)
    price_wholesale = db.Column(db.Float)

    ventas = db.Column(db.String(200))
    compras = db.Column(db.String(200))


class User(db.Model):
    __tablename__ = "user"
    idref = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(200))
    username = db.Column(db.String(200))
    password = db.Column(db.String(200))

    has_contact_info = db.Column(db.String(5))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(200))
    address = db.Column(db.String(200))
    CIF = db.Column(db.String(200))


db.create_all()
db.session.commit()

user_session = 0


@app.route('/', methods=['GET', 'POST'])
def home():
    if user_session == 0:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('products'))


@app.route('/profile')
def profile():
    return render_template('profile.html', user_session=user_session)


@app.route('/products')
def products():
    all_products = Producto.query.all()
    return render_template('index.html', user_session=user_session, product_list=all_products)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/contact_info', methods=['GET', 'POST'])
def contact_info():
    global user_session

    user_to_update = User.query.filter_by(username=user_session.username).first()
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    cif = request.form['CIF']

    if email != "" and phone != "" and address != "" and cif != "":
        user_to_update.has_contact_info = "yes"
        user_to_update.email = email
        user_to_update.phone = phone
        user_to_update.address = address
        user_to_update.CIF = cif

        db.session.commit()
        user_session = User.query.filter_by(username=user_session.username).first()

        return redirect(url_for('profile'))

    else:
        flash('All fields must be filled to update.')

        return redirect(url_for('profile'))


@app.route('/generate_random', methods=['GET', 'POST'])
def generate_random():
    all_products = Producto.query.all()
    for product in all_products:

        compras = []
        ventas = []
        stock = product.stock.split("/")

        for i in range(8):
            ventas.append(str(random.randrange(10, 100)))
            compras.append(str(random.randrange(1, int(ventas[i]))))

        product.compras = " ".join(compras)
        product.ventas = " ".join(ventas)
        product.opinions = str(random.randrange(1, 6)) + "/5"
        product.stock = str(random.randrange(int(int(stock[0])*0.8), int(stock[1]) + 1)) + "/" + stock[1]

        db.session.commit()

    return redirect(url_for('products'))


@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    all_products = Producto.query.all()
    all_users = User.query.all()
    product_and_iva = {}
    for i in all_users:
        product_and_iva[i.username] = [all_products[random.randrange(1, len(all_products))], str(random.randrange(9, 22))]
    return render_template('suppliers.html', product_list=all_products, user_list=all_users, user_session=user_session,
                           product_and_iva=product_and_iva)


@app.route('/product_info/<idref>')
def product_info(idref):

    product = Producto.query.filter_by(idref=idref).first()

    ventas = product.ventas.split()
    ventas = list(map(float, ventas))

    compras = product.compras.split()
    compras = list(map(float, compras))

    print(ventas)
    print(compras)

    global user_session
    if user_session.user_type == "Customer":
        values = ventas
        title = "Ventas"

    elif user_session.user_type == "Supplier":
        values = compras
        title = "Compras"

    elif user_session.user_type == "Admin":
        beneficios = []
        for i in range(8):
            beneficios.append(ventas[i] * product.price_retail - compras[i] * product.price_wholesale)
        values = beneficios
        title = "Beneficios"
            
    return render_template('product_info.html', user_session=user_session, product=product,
                           values=values, max=max(values), title=title)


@app.route('/register_action', methods=['GET', 'POST'])
def register():
    # main data variables
    user_type_collected = request.form['type_register']
    username = request.form['user_register']
    password = request.form['password_register']
    password_confirm = request.form['password_repeat_register']

    # variables to check whether valid or not
    username_isvalid = User.query.filter_by(username=username).first() is None and len(username) > 4
    password_isvalid = len(password) > 8 and password == password_confirm

    if username_isvalid and password_isvalid:
        new_account = User(
            user_type=user_type_collected,
            username=username,
            password=password,
            has_contact_info="no")
        db.session.add(new_account)
        db.session.commit()
        return redirect(url_for('login'))
    elif username_isvalid and not password_isvalid:
        flash('Password must be 9 characters or longer and match the "repeat password" field.')
        return redirect(url_for('login'))
    elif not username_isvalid and password_isvalid:
        flash('Username is taken or shorter than 5 characters.')
        return redirect(url_for('login'))
    elif not username_isvalid and not password_isvalid:
        flash('Password and username are not valid.')
        return redirect(url_for('login'))


@app.route('/login_action', methods=['GET', 'POST'])
def login_action():
    username = request.form["username_login"]
    password = request.form["password_login"]
    query_by_username = User.query.filter_by(username=username).first()

    if query_by_username is not None and query_by_username.password == password:
        global user_session
        user_session = query_by_username
        return redirect(url_for('home'))
    else:
        flash('Please check your login details and try again.')
        return redirect(url_for('login'))


'''

TEST TEST TEST TEST

username_isvalid = User.query.filter_by(username="adr").first()
print(username_isvalid)

PREGUNTAS PREGUNTAS PREGUNTAS 

como puedo redirigir a una tab concreta dentro de una pestaña
'''

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template , request, flash ,redirect

import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_file = ["settings.toml"])

app.secret_key = config.secret_key

def connect_db():
    conn = pymysql.connect(
        host="db.steamcenter.tech",
        user="jlewin",
        passwd= config.password,
        database="jlewin_riffts",
        autocommit = True,
        cursorclass = pymysql.cursors.DictCursor
    )# function for fetching the database quickly
    return conn




@app.route("/")
def index():
    return render_template("Homepage.html.jinja")

@app.route("/browse")
def browse():
    connection = connect_db()
    # This variable connects the page to the data base 
    cursor =connection.cursor()

    cursor.execute("SELECT * FROM `Product`")

    result = cursor.fetchall()

    connection.close
    return render_template("browse.html.jinja", products = result)

@app.route("/product/<product_id>")
def product_page(product_id):

    connection = connect_db()
    # This variable connects the page to the data base 
    cursor =connection.cursor()

    cursor.execute("SELECT * FROM `Product` WHERE `ID` = %s", ( product_id ))
    # %s is used for formating in SQL commands 

    result = cursor.fetchone()

    connection.close()

    return render_template("product.html.jinja", product = result)

@app.route("/register", methods = ['POST', 'GET'])
def register():
    if request.method == 'POST':

        name =request.form ["name"]

        email = request.form ["email"]

        password = request.form ["password"]

        confirm_password = request.form ['confirm_password']

        birthday = request.form ['birthday']

        if password != confirm_password:
            flash("passowrd doesn't match")
        elif len(password) < 8:
            flash("password is too short")
        else:
            connection = connect_db()

            cursor = connection.cursor()

            cursor.execute(
            """
            INSERT INTO `User` ( `Name`, `Password`,`Email,`BirthDate`)
            VALUES (%s, %s, %s, %s)
            """, (name, password, email, birthday))
            
            return "thank you for signing up"
        
        print(request.form["password"])
    return render_template("register.html.jinja")

@app.route("/login")
def login():
    
    return render_template("login.html.jinja")
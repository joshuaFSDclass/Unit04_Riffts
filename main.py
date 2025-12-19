from flask import Flask, render_template , request, flash ,redirect, abort
from flask_login import LoginManager, login_user, logout_user, login_required,current_user
import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_file = ["settings.toml"])

app.secret_key = config.secret_key

login_mannager = LoginManager( app )

login_mannager.login_view = '/login'

class User:
    is_authenticated =True
    is_active = True
    is_anonymous = False

    def __init__ (self, result):
        self.name = result ['Name']
        self.email = result ['Email']
        self.birthday = result['BirthDate']
        self.id = result ['ID']

    def get_id(self):
        return str(self.id)

@login_mannager.user_loader
def local_user(user_id):
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(" SELECT  * FROM `User` WHERE `ID` = %s", (user_id) )

    result = cursor.fetchone()

    connection.close

    if result is None:
        return None
    
    return User(result)

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

    if result is None:
        abort(404)

    return render_template("product.html.jinja", product = result)

@app.route("/product/<product_id>/add_to_cart", methods =['POST'])
@login_required
def add_to_cart(product_id):

    quantity = request.form['QTY']

    connection = connect_db()
    # This variable connects the page to the data base 
    cursor =connection.cursor()

    cursor.execute(
        """INSERT INTO `Cart` (`Quantity`, `ProductID`,`UserID`)  
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        `Quantity` = `Quantity` + %s
        """, (quantity, product_id, current_user.id, quantity))

    connection.close()
    return redirect("/cart")



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

            try:
                
                cursor.execute(
                """
                INSERT INTO `User` ( `Name`, `Password`,`Email`,`BirthDate`)
                VALUES (%s, %s, %s, %s)
                """, (name, password, email, birthday))
                connection.close()
            except pymysql.err.IntegrityError:
                flash("User with that email already exists")
                connection.close()
                return "thank you for signing up"
            else:
                return redirect('/login')

        print(request.form["password"])
    return render_template("register.html.jinja")

@app.route("/login", methods = ['POST', 'GET'] )
def login():

    if request.method == 'POST':

        email = request.form ['email']

        password = request.form ['password']

        connection = connect_db()

        cursor = connection.cursor()

        cursor.execute(" SELECT * FROM `User` WHERE `Email` = %s ", ( email ))

        result = cursor.fetchone()

        connection.close()
        
        if result is None:
            flash("No user found")
        elif password is result["Password"]:
            flash("Incorrect password")
        else:
            login_user(User(result))
            return redirect('/browse')

    return render_template("login.html.jinja")

@app.route("/logout", methods = ['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect("/")
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

    if result is None:
        abort(404)

    cursor.execute(""" 
    SELECT * FROM `Review`  
    JOIN `User` ON `Review`.`UserID`= `User`.`ID` 
    WHERE `ProductID` = %s""", (product_id))

    reviews = cursor.fetchall()

    connection.close()

    avgReview = 0 

    for item in reviews:
        avgReview += item["Rattings"] 
    
    avgReview = avgReview / len(reviews)

    return render_template("product.html.jinja", product = result, reviews = reviews, avgReview = avgReview)

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


@app.route("/product/<product_id>/review", methods = ["POST"])
@login_required
def add_review(product_id):
    #get input valuesfrom the form
    rating = request.form["Rattings"]
    comments = request.form["WrittenReview"]
    #connect to the database
    connection = connect_db()
    cursor = connection.cursor()
    #add the review to the database 
    cursor.execute("""
    INSERT INTO `Review`
                (`Rattings`, `WrittenReview`, `UserID`, `ProductID`)
                VALUES
                (%s,%s,%s,%s)
                   """,(rating, comments, current_user.id, product_id))
    return redirect(f"/product/{product_id}")


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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/cart")
@login_required
def Cart():
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM `Cart`
        JOIN `Product` ON `Product` . `ID` = `Cart` . `ProductID`
        WHERE `UserID` = %s
        """, (current_user.id))
    
    result = cursor.fetchall()
    
    total = 0 

    for item in result:
        total += item["Price"] * item["Quantity"]
    connection.close()
    return render_template("Cart.html.jinja", cart = result, total = total)

@app.route("/cart/<product_id>/update", methods=["POST"])
def update_cart(product_id):
    new_qty = request.form['qty']

    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE `Cart`
        SET `Quantity` = %s
        WHERE `ProductID` = %s AND `UserID` = %s

        """, (new_qty, product_id, current_user.id)

    )
    connection.close()
    
    return redirect("/cart")


@app.route("/cart/<product_id>/remove", methods = ["POST"])
@login_required
def remove_item(product_id):

    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM `Cart`
        WHERE `ProductID` = %s AND `UserID` = %s
        
        """,(product_id, current_user.id)
    )
    connection.close()

    return redirect("/cart")

@app.route("/checkout", methods = ["POST", "GET"])
@login_required
def checkout():
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM `Cart`
        JOIN `Product` ON `Product` . `ID` = `Cart` . `ProductID`
        WHERE `UserID` = %s
        """, (current_user.id))
    
    result = cursor.fetchall()
    
    total = 0 

    for item in result:
        total += item["Price"] * item["Quantity"]

    if request.method =="POST":
        cursor.execute( "INSERT INTO `Sale` (`UserID`) VALUES (%s)", (current_user.id) )
        sale = cursor.lastrowid
        for item in result:
            cursor.execute("""
            INSERT INTO `SaleCart` 
            (`SaleID`,`ProductID`, `Quantity`)
            VALUES
            (%s,%s,%s)
            """,(sale, item ['ProductID'], item['Quantity']) )
        cursor.execute("DELETE FROM `Cart` WHERE `UserID` = %s", (current_user.id,))
        return redirect("/thankyou")

    connection.close()
    return render_template("Checkout.html.jinja", cart = result, total = total)
@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html.jinja")

@app.route("/OrderPage")
@login_required
def OrderPage():
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute(
    """
    SELECT 
        `Sale`.`ID`,
        `Sale`.`Timestamp`,
        SUM(`SaleCart`.`Quantity`) AS 'Quantity',
        SUM(`SaleCart`.`Quantity` * `Product`.`Price`) AS 'Total'
    FROM `Sale`
    JOIN `SaleCart` ON `SaleCart`.`SaleID` = `Sale`.`ID`
    JOIN `Product` ON `Product`.`ID` = `SaleCart`.`ProductID`
    WHERE `UserID` = %s
    GROUP BY `Sale`.`ID`;
    """,(current_user.id, ))

    result = cursor.fetchall()

    connection.close()

    return render_template("Orderpage.html.jinja", Orders = result)

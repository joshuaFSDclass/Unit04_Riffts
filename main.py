from flask import Flask, render_template

import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_file = ["settings.toml"])

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

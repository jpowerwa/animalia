#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

import json

from flask import Flask, render_template, request
from flask.ext.mysql import MySQL

app = Flask(__name__)
app.debug = True


mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'animalia'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/show_signup')
def show_signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['input_name']
    email = request.form['input_email']
    password = request.form['input_password']
    if not (name and email and password):
        return json.dumps({'html':'<span>Enter the required fields</span>'})
    else:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.callproc('sp_createUser', (name, email, password))
        data = cursor.fetchall()
        if len(data) is 0:
            conn.commit()
            return json.dumps({'message':'User created successfully !'})
        else:
            return json.dumps({'error':str(data[0])})



if __name__ == "__main__":
    app.run()

from crypt import methods
from typing import List, Dict
from flask import Flask, render_template, request, make_response, request, jsonify, url_for, session, redirect
from flask_mysqldb import MySQL
import MySQLdb.cursors
from passlib.hash import sha256_crypt
from werkzeug.exceptions import HTTPException
import secrets
import mysql.connector
import json
import re
import os
import smtplib
import os
import random as rd


app = Flask(__name__)

## ______________________________ Initial Configuration ______________________________

# Enter your database connection details below
app.config['MYSQL_HOST'] = os.getenv('DB_HOST', 'db')
app.config['MYSQL_USER'] = os.getenv('DB_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD', 'root')
app.config['MYSQL_DB'] = os.getenv('DB_DB', 'pythonlogin')
app.config['MYSQL_PORT'] = 3306

# Intialize MySQL
mysql = MySQL(app)

# Extract data for email sending
sender = os.environ.get('SENDER_MAIL')
print("Sender Mail: ", sender)
password = os.environ.get('APP_PASSWORD')

with open("./mail.json", "r") as f:
    data = json.load(f)
mail_subject = data["mail_subject"]
mail_body = data["mail_body"]


# Extract the question data
with open("./question.json", "r") as f:
    data = json.load(f)
answers = data["answers"]

## ______________________________ Pages ______________________________

# Home Page
@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
    
# Login endpoint
@app.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        
        if account:
            if sha256_crypt.verify(password, account['password']):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['mail'] = account['mail']
                session['hasFound'] = account['hasFound']
                session['discoverTime'] = account['discoverTime']
                # Redirect to home page
                return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    
    return render_template('login.html', msg=msg)
  
# Lougout endpoint    
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('mail', None)
   session.pop('discoverTime', None)
   # Redirect to login page
   return redirect(url_for('login'))

# Register endpoint
@app.route('/login/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    previous_mail = ''

    # Check if "mail", "password", "answer" POST requests exist (user submitted form)
    if request.method == 'POST' and 'mail' in request.form and 'password' in request.form and 'answer' in request.form:
        # Create variables for easy access
        mail = request.form['mail']
        password = sha256_crypt.encrypt(request.form['password'])
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE mail = %s', (mail,))
        account = cursor.fetchone()
        
        answer = request.form['answer']
        if not mail or not password or not answer:
            msg = 'Please fill out the form!'
        elif "@telecom-sudparis.eu" not in mail and "@imt-bs.eu" not in mail: # Check if it is a TSP or IMT-BS adress
            msg = 'Please use your TSP or IMT-BS mail address'
        elif account: # If account exists show error and validation checks
            msg = 'Account already exists!'
        elif answer not in answers: # If the answer is wrong the account is not created
            msg = 'Wrong answer !'
            previous_mail = mail
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            return redirect(url_for('verification', receiver=mail))
            # cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, 0, %s, DEFAULT)', (mail, password,))
            # mysql.connection.commit()
            
            
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg, previous_mail=previous_mail)



@app.route('/login/register/verification', methods=['GET', 'POST'])
def verification():
    # Output message if something goes wrong...
    msg = ''

    receiver = request.args.get('receiver')
    print(receiver)
    
    code = sent_code(receiver=receiver)

    if request.method == 'POST' and 'send-code' in request.form:
        pressed_button = request.form['button']
        if pressed_button == 'Validate':
            return render_template('register.html', msg='Account created successfully')
            pass
        elif pressed_button == 'button2':
            code = sent_code()
            pass

    return render_template('verification.html', msg=msg, maxlength=len(code))


def sent_code(receiver):
    code = ''
    codelength = 6
    for i in range(codelength):
        code += str(rd.randrange(0, 10))
    
    body = mail_body + code

    mail = f'Suject: {mail_subject}\n\n{body}'

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(sender, password)
        print("Login completed")


        smtp.sendmail(sender, receiver, mail)
        print("Email envoyé")
    
    return code







# Items page
@app.route('/<string:slug>')
def seeItem(slug):
    if 'loggedin' in session:
        slugList = [item["slug"] for item in items]
        if slug in slugList:
            id = slugList.index(slug)
            
            if session["inventory"][id] == "0":
                # First time seeing the card
                hasAlreadySeen = False
                
                # Change inventory and score
                session["inventory"] = session["inventory"][0:id] + "1" + session["inventory"][id+1: ]
                session["score"] = str( int(session["score"]) + items[id]["pointsMin"] )
                
                # Update database
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
                account = cursor.fetchone()
                
                if account:
                    cursor.execute('UPDATE accounts SET score = %s, inventory = %s WHERE id = %s', (session["score"], session["inventory"], session["id"],))
                    mysql.connection.commit()
                else:
                    return "You're not logged in are you ?"
                
            else:
                hasAlreadySeen = True
            return render_template('item.html', item=items[id], hasAlreadySeen=hasAlreadySeen)
    
    return redirect(url_for('home'))
    
# Scoreboard page
@app.route('/scoreboard')
def scoreboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT username, score FROM accounts ORDER BY score DESC, lastScanTime ASC')
    rows = cursor.fetchall()
    
    return render_template('scoreboard.html', rows=rows)
    


if __name__ == '__main__':
    app.run(debug = False, host='0.0.0.0')

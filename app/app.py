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

app = Flask(__name__)

# Secret key
# DON'T SHOW THIS TO ANYONE
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = os.getenv('DB_HOST', 'db')
app.config['MYSQL_USER'] = os.getenv('DB_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD', 'root')
app.config['MYSQL_DB'] = os.getenv('DB_DB', 'pythonlogin')
app.config['MYSQL_PORT'] = 3306

# Intialize MySQL
mysql = MySQL(app)

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



# Extract the question data
with open("./question.json", "r") as f:
    data = json.load(f)
answers = data["answers"]


# Register endpoint
@app.route('/login/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
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
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            return redirect(url_for('verification'))
            # cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, 0, %s, DEFAULT)', (mail, password,))
            # mysql.connection.commit()
            
            
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)



@app.route('/login/register/verification', methods=['GET', 'POST'])
def verification():
    # Output message if something goes wrong...
    msg = ''
    if firstVerification == None or firstVerification:
        firstVerification = False











    return render_template('verification.html', msg=msg)


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, message):
    # Paramètres du serveur SMTP
    smtp_server = 'smtp.example.com'
    smtp_port = 587  # Port SMTP (peut être 465 pour SSL)

    # Adresse e-mail et mot de passe de l'expéditeur
    sender_email = 'thomas.schneider@telecom-sudparis.eu'
    password = 'your_password'

    # Création du message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Ajout du corps du message
    msg.attach(MIMEText(message, 'plain'))

    # Connexion au serveur SMTP
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Pour sécuriser la connexion
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, msg.as_string())




with open("./mail.json", "r") as f:
    data = json.load(f)
answers = data["password"]



















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

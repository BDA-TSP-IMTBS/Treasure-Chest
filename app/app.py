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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


app = Flask(__name__)

## ______________________________ Initial Configuration ______________________________
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

# Extract data for email sending
sender = os.environ.get('SENDER_MAIL')
print("Sender Mail: ", sender)
app_password = os.environ.get('APP_PASSWORD')

with open("./mail.json", "r") as f:
    data = json.load(f)
mail_subject = data["mail_subject"]
mail_body = data["mail_body"]


# Extract the question data
with open("./question.json", "r") as f:
    data = json.load(f)
questionImage = data["image"]
question = data["question"]
answers = data["answers"]


# Extract the treasures data
with open("./treasures.json", "r") as f:
    data = json.load(f)
final_enigme = data["final-enigme"]
treasure_code = data["code"]
treasures = data["treasures"]
toolate = data["too-late"]

## ______________________________ Pages ______________________________

# Home Page
@app.route('/', methods=['GET', 'POST'])
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        msg = ''
        
        # User is loggedin show them the home page
        if request.method == 'POST' and 'code' in request.form:

            code = request.form['code']
            if code == treasure_code:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
                account = cursor.fetchone()

                if account['hasFound'] == False:
                    session['hasFound'] = True
                    session['discoverTime'] = datetime.now().isoformat()
                    cursor.execute("SELECT COUNT(*) from accounts WHERE hasFound=%s", (True,))
                    tmp = str(cursor.fetchone())
                    session['place'] = int(tmp.split(':')[1][:-1]) + 1


                    cursor.execute('UPDATE accounts SET hasFound = %s, discoverTime = %s, place = %s WHERE id = %s', (session["hasFound"], session["discoverTime"], session['place'], session["id"], ))
                    mysql.connection.commit()

                    for i in range(len(treasures)):
                        if session['place'] in treasures[i]["places"]:
                            return redirect(url_for('treasure', slug=treasures[i]["slug"]))
                    
                    return redirect(url_for('treasure', slug=toolate["slug"]))
                
                else:
                    msg = "You already found the treasure"
            
            else:
                msg = "Wrong code !"
        
        prenom = session['mail'].split('.')[0]
        return render_template('home.html', prenom=prenom[0].upper() + prenom[1:], final_enigme=final_enigme, msg=msg)
    
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# Login endpoint
@app.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'mail' in request.form and 'password' in request.form:
        mail = request.form['mail']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE mail = %s', (mail,))
        account = cursor.fetchone()
        
        if account:
            if sha256_crypt.verify(password, account['password']):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['mail'] = account['mail']
                session['hasFound'] = account['hasFound']
                session['place'] = account['place']
                session['discoverTime'] = account['discoverTime']
                # Redirect to home page
                return redirect(url_for('home'))
        else:
            # Account doesnt exist or mail/password incorrect
            msg = 'Incorrect mail/password!'
    
    return render_template('login.html', msg=msg)

# Lougout endpoint    
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('mail', None)
   session.pop('place', None)
   session.pop('discoverTime', None)
   # Redirect to login page
   return redirect(url_for('login'))

# Register endpoint
@app.route('/login/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    if request.args.get('msg') != None:
        msg = request.args.get('msg')
    else:
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
        
        answer = request.form['answer'].lower()

        if account: # If account exists show error and validation checks
            msg = 'Account already exists!'
        elif "@telecom-sudparis.eu" not in mail and "@imt-bs.eu" not in mail: # and "!!" not in mail: # Check if it is a TSP or IMT-BS adress
            msg = 'Use your TSP or IMT-BS mail adress'
        elif not mail or not password or not answer:
            msg = 'Please fill out the form!'
            previous_mail = mail
        elif answer not in answers: # If the answer is wrong the account is not created
            msg = 'Wrong answer !'
            previous_mail = mail
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            session['firstverification'] = True
            session['receiver'] = mail
            session['tmp_pass'] = password
            return redirect(url_for('verification'))
            
            
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg, previous_mail=previous_mail, question=question, questionImage=questionImage)

# Verification endpoint
@app.route('/login/register/verification', methods=['GET', 'POST'])
def verification():
    # Output message if something goes wrong...
    msg = ''

    if session['firstverification'] == True:
        receiver = session['receiver']
        code = send_code(receiver)
        session['firstverification'] = False
        session['code'] = code
        pass
    else:
        code = session['code']

    if request.method == 'POST' and 'code' in request.form:

        pressed_button = request.form['button']
        if pressed_button == 'Validate':
            received_code = request.form['code']
            if received_code == code:
                mail = session['receiver']
                password = session['tmp_pass']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, 0, DEFAULT)', (mail, password, False))
                mysql.connection.commit()

                # Clear session values used for verification
                session.pop('receiver', None)
                session.pop('tmp_pass', None)
                session.pop('firstverification', None)

                return redirect(url_for('register', msg='Account successfully created'))
            
            else:
                msg = 'Wrong code ' #+ code
            pass

        elif pressed_button == 'Resent code':
            session['firstverification'] = True
            msg = 'Code resent'
            pass

    return render_template('verification.html', msg=msg, maxlength=len(code))

def send_code(receiver):
    # Création du code à envoyer
    code = ''
    codelength = 6
    for i in range(codelength):
        code += str(rd.randrange(0, 10))
    body = mail_body + code

    # Créer le message
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = mail_subject

    # Ajouter le corps du message
    msg.attach(MIMEText(body, 'plain'))

    # Convertir le message en chaîne de caractères
    mail = msg.as_string()

    # Envoie du mail
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(sender, app_password)
        print("Login completed")

        try:
            smtp.sendmail(sender, receiver, mail)
            print("Email envoyé")
        except:
            return redirect(url_for('register', msg='Wrong email address'))
    
    return code

# Treasures page
@app.route('/<string:slug>')
def treasure(slug):
    if 'loggedin' in session:

        slugList = [treasure["slug"] for treasure in treasures]

        if slug in slugList:
            id = slugList.index(slug)

            return render_template('treasure.html', treasure = treasures[id], coffre="Plage-Ouvert.png")
        elif slug == 'too-late':
            return render_template('treasure.html', treasure = toolate, coffre="Plage-Vide.png")

    
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# TreasureFound page
@app.route('/foundtreasure')
def foundtreasure():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        if account['hasFound'] == True:
            for i in range(len(treasures)):
                if session['place'] in treasures[i]["places"]:
                    return redirect(url_for('treasure', slug=treasures[i]["slug"]))
            
            return redirect(url_for('treasure', slug=toolate["slug"]))
        
        else:
            return render_template('nothing.html')
            
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# Scoreboard page
@app.route('/scoreboard')
def scoreboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT mail, place, discoverTime FROM accounts WHERE hasFound=%s ORDER BY place ASC", (True,))
    founds = cursor.fetchall()

    cursor.execute("SELECT mail FROM accounts WHERE hasFound=%s", (False,))
    notFounds = cursor.fetchall()


    
    return render_template('scoreboard.html', founds=founds, notFounds=notFounds)



if __name__ == '__main__':
    app.run(debug = False, host='0.0.0.0')

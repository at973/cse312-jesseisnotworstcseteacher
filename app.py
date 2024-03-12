from flask import Flask, render_template, send_from_directory, make_response, redirect, url_for, request
import mysql.connector
import bcrypt
import secrets
import hashlib
import time 

app = Flask(__name__)

time.sleep(3)

db = mysql.connector.connect(host='oursql', user='user', passwd='password', database='mysql')
mycursor = db.cursor()

@app.route('/') #Returns templates/index.html
def index():
    if 'auth_token' in request.cookies:
        hashed_auth = hashlib.sha256(request.cookies.get('auth_token').encode()).hexdigest
        mycursor.execute('SELECT * FROM User')
        for i in mycursor:
            if i[2]:
                if i[2] == hashed_auth:
                    mycursor.execute('SELECT * FROM Token')
                    for i in mycursor:
                        if i[0]:
                            if i[0] == hashed_auth:
                                if i[1]:            
                                    f = open("templates/index.html", "rb")
                                    body = f.read()
                                    stringbody = body.decode()
                                    stringbody = stringbody.replace('Not Logged In', i[0])
                                    return make_response(stringbody)
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def giveRegister():
    username = request.form.get('username')
    password = request.form.get('password')
    same_password = request.form.get('password2')
    if password == same_password:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        mycursor.execute('CREATE Table IF NOT EXISTS User (username VARCHAR(20), password VARCHAR(100), auth_token VARCHAR(100), ID int PRIMARY KEY AUTO_INCREMENT)')
        mycursor.execute('SELECT * FROM User')
        exist = False
        for i in mycursor:
            if i[0] == username:
                exist = True
        if exist == False:
            mycursor.execute('INSERT INTO User (username, password, auth_token) VALUES(%s,%s, %s)', (username, hashed_password, 'no auth'))
        db.commit()
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def giveLogin():
    response = make_response(redirect(url_for('index')))
    username = request.form.get('username')
    password = request.form.get('password')
    mycursor.execute('CREATE Table IF NOT EXISTS User (username VARCHAR(20), password VARCHAR(100), auth_token VARCHAR(100), ID int PRIMARY KEY AUTO_INCREMENT)')
    mycursor.execute('CREATE Table IF NOT EXISTS Token (auth_token VARCHAR, exist BOOLEAN)')
    mycursor.execute('SELECT * FROM User')
    auth_token = secrets.token_hex(20)
    hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
    mycursor.execute('INSERT INTO Token (auth_token, exist) VALUES(%s,%s)', (hashed_auth, True))
    for i in mycursor:
        if i[0] == username and bcrypt.checkpw(i[1].encode(), password):
            update(hashed_auth, username)
            response.set_cookie('auth_token', auth_token, max_age=7200)
            return response
    return response

@app.route('/logout', methods=['POST'])
def giveLogout():
    if 'auth_token' in request.cookies:
        auth_token = request.cookies.get('auth_token')
        hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
        update_token(hashed_auth)
        request.cookies.pop('auth_token')
    return make_response(redirect(url_for('index')))

@app.route('/createpost', methods=['POST'])
def createPost():
    auth = request.cookies.get('auth_token')
    message = request.form.get('message')
    message = message.replace("&", "&amp;") #Replaces & with html safe version
    message = message.replace(">", "&gt;") #Replaces > with html safe version
    message = message.replace("<", "&lt;") #Replaces < with html safe version
    message = message.replace("\"", "&quot;") #Replaces " with html safe version
    script = 'CREATE Table if not exists Posts (username VARCHAR(20), message TEXT, ID int PRIMARY KEY AUTO_INCREMENT)'
    mycursor.execute()
    if auth is not None:
        script = 'SELECT * from Token where auth_token = ' + auth        
        mycursor.execute(script)
        data = mycursor.fetchone() #data[0] = auth_token data[1] = exist
        if data[1] == True: #If auth token and proper auth token, create post
            script = 'Select username from User where auth_token = ' + auth
            mycursor.execute(script)
            username = mycursor.fetchone()[0] 
            script = 'INSERT into Posts (username, message), VALUES(%s, %s)'
            mycursor.execute(script, (username, message))
    db.commit() 

def update(auth_token, username):
    mycursor.execute('UPDATE User SET auth_token = %s WHERE username = %s', (auth_token, username))
    db.commit

def update_token(auth_token):
    mycursor.execute('UPDATE Token SET exist = %s WHERE auth_token = %s', (False, auth_token))
    db.commit 


@app.route('/css/<css>') #Returns any file from css directory
def giveCSS(css):
    return send_from_directory('css', css)

@app.route('/js/<js>') #Returns any file from js directory
def giveJS(js):
    return send_from_directory('js', js)

@app.route('/images/<images>') #Returns any file from images directory
def giveImage(images):
    return send_from_directory('images', images)

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=8080)

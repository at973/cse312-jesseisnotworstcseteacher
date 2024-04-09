from flask import Flask, render_template, send_from_directory, make_response, redirect, url_for, request, jsonify, Response
import mysql.connector
import bcrypt
import secrets
import hashlib
import time 

app = Flask(__name__)


success = False

while not success:
    time.sleep(3)
    try:
        db = mysql.connector.connect(host='oursql', user='user', passwd='password', database='mysql')
        success = True
    except:
        pass
mycursor = db.cursor(buffered=True)

@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/') #Returns templates/index.html
def index():
    username='guest'
    if 'auth_token' in request.cookies:
        hashed_auth = hashlib.sha256(request.cookies.get('auth_token').encode()).hexdigest()
        if (not table_exist('User')):
            mycursor.execute('CREATE Table IF NOT EXISTS User (username TEXT, password TEXT, auth_token TEXT, ID int PRIMARY KEY AUTO_INCREMENT)')
            db.commit()
        mycursor.execute('SELECT * FROM User WHERE auth_token = %s', (hashed_auth,))
        user = mycursor.fetchone()
        # print("fuck it, here's the whole database", mycursor.fetchall())
        # print('username displayed: ', user, 'auth_token received:', hashed_auth)
        if user:
            username = user[0]
            mycursor.execute('SELECT * FROM Token WHERE auth_token = %s', (hashed_auth,))
            token = mycursor.fetchone()
            # if token:
            #     if token[1]:
            #         with open("templates/index.html", "r") as f:
            #             stringbody = f.read()
            #             stringbody = stringbody.replace('Guest', username)
            #         return make_response(stringbody)
    response =  Response(render_template('index.html', username=username))
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/register', methods=['POST'])
def giveRegister():
    username = request.form.get('username')
    password = request.form.get('password')
    same_password = request.form.get('password2')
    if password == same_password:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        if (not table_exist('User')):
            mycursor.execute('CREATE Table IF NOT EXISTS User (username TEXT, password TEXT, auth_token TEXT, ID int PRIMARY KEY AUTO_INCREMENT)')
            db.commit()
        mycursor.execute('SELECT * FROM User')
        exist = False
        for i in mycursor:
            if i[0] == username:
                exist = True
        if exist == False:
            mycursor.execute('INSERT INTO User (username, password, auth_token) VALUES(%s,%s, %s)', (username, hashed_password, 'no auth'))
        db.commit()
    # response = Response(redirect(url_for('index')))
    # response.headers['X-Content-Type-Options'] = 'nosniff'
    # return response
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def giveLogin():
    response = make_response(redirect(url_for('index')))
    username = request.form.get('username')
    password = request.form.get('password')
    userTable = table_exist('User')
    tokenTable = table_exist('Token')
    if userTable and tokenTable:
        mycursor.execute('SELECT * FROM User')
        auth_token = secrets.token_hex(20)
        hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
        mycursor.execute('SELECT * FROM User WHERE username = %s', (username,))
        exist = mycursor.fetchone()
        if exist:
            hashed_password = exist[1]
            if bcrypt.checkpw(password.encode(), hashed_password.encode()):
                mycursor.execute('INSERT INTO Token (auth_token, exist) VALUES(%s, %s)', (hashed_auth, True))
                update(hashed_auth, username)
                response.set_cookie('auth_token', auth_token, max_age=7200)
                return response
        return response
    else:
        if not userTable:
            mycursor.execute('CREATE Table IF NOT EXISTS User (username TEXT, password TEXT, auth_token TEXT, ID int PRIMARY KEY AUTO_INCREMENT)')
            db.commit()
        if not tokenTable:
            mycursor.execute('CREATE Table IF NOT EXISTS Token (auth_token TEXT, exist BOOLEAN)')
            db.commit()
        mycursor.execute('SELECT * FROM User')
        auth_token = secrets.token_hex(20)
        hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
        mycursor.execute('SELECT * FROM User WHERE username = %s', (username,))
        exist = mycursor.fetchone()
        if exist:
            hashed_password = exist['password']
            if bcrypt.checkpw(password.encode(), hashed_password):
                mycursor.execute('INSERT INTO Token (auth_token, exist) VALUES(%s,%s)', (hashed_auth, True))
                update(hashed_auth, username)
                response.set_cookie('auth_token', auth_token, max_age=7200)
                return response
        return response

@app.route('/logout', methods=['POST'])
def giveLogout():
    response = make_response(redirect(url_for('index')))
    if 'auth_token' in request.cookies:
        auth_token = request.cookies.get('auth_token')
        hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
        update_token(hashed_auth)
        response.set_cookie('auth_token', '', expires=0)
    return response

@app.route('/createpost', methods=['POST'])
def createPost():
    #Create post should be called via html form
    auth = request.cookies.get('auth_token')
    print("Auth is: " + str(auth))
    message = request.form.get('message')
    print("Message is: " + str(message))
    message = message.replace("&", "&amp;") #Replaces & with html safe version
    message = message.replace(">", "&gt;") #Replaces > with html safe version
    message = message.replace("<", "&lt;") #Replaces < with html safe version
    message = message.replace("\"", "&quot;") #Replaces " with html safe version

    if not table_exist('Posts'):
        script = 'CREATE Table if not exists Posts (username TEXT, message TEXT, ID int AUTO_INCREMENT, PRIMARY KEY (ID))'
        mycursor.execute(script)
        db.commit()

    # testCreate() #MUST REMOVE, JUST FOR TESTING!!!

    if auth is not None:
        hashed_auth = hashlib.sha256(auth.encode()).hexdigest()
        print("Hashed auth is: " + str(hashed_auth))
        if not table_exist("Token"):
            mycursor.execute('CREATE Table IF NOT EXISTS Token (auth_token TEXT, exist BOOLEAN)')
            db.commit()
        mycursor.execute('SELECT * from Token')
        print(mycursor.fetchall())
        script = 'SELECT * from Token where auth_token = %s'
        mycursor.execute(script, (hashed_auth,))
        data = mycursor.fetchone() #data[0] = auth_token data[1] = exist
        if data != None:
            print(data)
            if data[1] == True: #If auth token and proper auth token, create post
                script = 'Select username from User where auth_token = %s'
                mycursor.execute(script, (hashed_auth,))
                username = mycursor.fetchone()
                if username is not None:
                    script = 'INSERT into Posts (username, message) VALUES(%s, %s)'
                    username = username[0]
                    mycursor.execute(script, (username, message))
                    db.commit()
    response = make_response(redirect(url_for('index'))) #Return 200
    return response


@app.route('/like', methods=['POST'])
def createLike():
    #Create post should be called via html form
    auth = request.cookies.get('auth_token')
    id = request.form.get('id')
    if not table_exist('Likes'):
        mycursor.execute('CREATE Table IF NOT EXISTS Likes (ID int, username TEXT)')
        db.commit()

    if auth is not None and id is not None:
        hashed_auth = hashlib.sha256(auth.encode()).hexdigest()
        mycursor.execute('SELECT * from Token')
        script = 'SELECT * from Token where auth_token = %s'
        mycursor.execute(script, (hashed_auth,))
        data = mycursor.fetchone() #data[0] = auth_token data[1] = exist
        if data[1] == True: #If auth token and proper auth token, create post
            script = 'Select username from User where auth_token = %s'
            mycursor.execute(script, (hashed_auth,))
            username = mycursor.fetchone()
            if username is not None:
                script = 'SELECT * from Likes WHERE ID = %s'
                mycursor.execute(script, (id,))
                data = mycursor.fetchall()
                for line in data:
                    if line[1] == username[0]:
                        response = make_response(redirect(url_for('index'))) #Return 200
                        return response
                script = 'INSERT into Likes (ID, username) VALUES(%s, %s)'
                mycursor.execute(script, (id, username[0],))
                db.commit()
    response = make_response(redirect(url_for('index'))) #Return 200
    return response

def testCreate():
    script = 'INSERT into Posts (username, message) VALUES(%s, %s)'
    mycursor.execute(script, ("Gamer1", "Message1"))
    db.commit()
    script = 'INSERT into Posts (username, message) VALUES(%s, %s)'
    mycursor.execute(script, ("Gamer2", "Message2"))
    db.commit()
    script = 'INSERT into Posts (username, message) VALUES(%s, %s)'
    mycursor.execute(script, ("Gamer3", "Message3"))
    db.commit()

def fetchLikes(id):
    if not table_exist('Likes'):
        return 0
    script = 'SELECT * from Likes WHERE ID = %s'
    mycursor.execute(script, (id,))
    data = mycursor.fetchall()
    likes = len(data)
    return likes

@app.route('/messages', methods=['GET'])
def readMessages():
    if not table_exist('Posts'):
        script = 'CREATE Table if not exists Posts (username TEXT, message TEXT, ID int AUTO_INCREMENT, PRIMARY KEY (ID))'
        mycursor.execute(script)
        db.commit()
    script = 'SELECT username, message, id from Posts ORDER BY id DESC'
    mycursor.execute(script)
    data = mycursor.fetchall()
    result = []
    for line in data:
        result.append({"message": line[1], "username": line[0], "id": str(line[2]), "likes": str(fetchLikes(line[2]))})
        # result.append({"message": line[1], "username": line[0], "id": line[3]})
    return jsonify(result)

def update(auth_token, username):
    mycursor.execute('UPDATE User SET auth_token = %s WHERE username = %s', (auth_token, username))
    db.commit

def update_token(auth_token):
    mycursor.execute('UPDATE Token SET exist = %s WHERE auth_token = %s', (False, auth_token))
    db.commit 

def table_exist(name: str):
    mycursor.execute("SHOW TABLES LIKE '" + name + "'")
    table = mycursor.fetchone()
    if table:
        return True
    return False


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

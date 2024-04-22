from flask import Flask, render_template, send_from_directory, make_response, redirect, url_for, request, jsonify, Response
# from flask_sock import Sock
from flask_socketio import SocketIO, emit
import json
import mysql.connector
import bcrypt
import secrets
import hashlib
import time 

app = Flask(__name__)
# sock = Sock(app)
socketio = SocketIO(app)
clients = {}

config = {
    'host': 'oursql',
    'user': 'user', 
    'passwd': 'password',
    'database': 'mysql'
}

# success = False

# while not success:
#     time.sleep(3)
#     try:
#         db = mysql.connector.connect(host='oursql', user='user', passwd='password', database='mysql')
#         success = True
#     except:
#         pass
# mycursor = db.cursor()

@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

def connect_to_database():
    Success = False
    while not Success:
        try:
            connection = mysql.connector.connect(**config)
            Success = True
        except:
            print("waiting 3 seconds for mysql container to start...")
            time.sleep(3)
    cursor = connection.cursor()
    return connection, cursor

def get_username():
    if 'auth_token' in request.cookies:
        connection, cursor = connect_to_database()
        hashed_auth = hashlib.sha256(request.cookies.get('auth_token').encode()).hexdigest()
        if (not table_exist('User',cursor)):
            cursor.execute('CREATE Table IF NOT EXISTS User (username TEXT, password TEXT, auth_token TEXT, ID int PRIMARY KEY AUTO_INCREMENT)')
            connection.commit()
        cursor.execute('SELECT * FROM User WHERE auth_token = %s', (hashed_auth,))
        user = cursor.fetchall()
        if len(user) != 0:
            user = user[0]
            return user
        connection.close()
    return None

@app.route('/') #Returns templates/index.html
def index():
    username='guest'
    if 'auth_token' in request.cookies:
        connection, cursor = connect_to_database()
        hashed_auth = hashlib.sha256(request.cookies.get('auth_token').encode()).hexdigest()
        if (not table_exist('User',cursor)):
            cursor.execute('CREATE Table IF NOT EXISTS User (username TEXT, password TEXT, auth_token TEXT, ID int PRIMARY KEY AUTO_INCREMENT)')
            connection.commit()
        cursor.execute('SELECT * FROM User WHERE auth_token = %s', (hashed_auth,))
        user = cursor.fetchall()
        if len(user) != 0:
            user = user[0]
            username = user[0]
            cursor.execute('SELECT * FROM Token WHERE auth_token = %s', (hashed_auth,))
            token = cursor.fetchall()[0]
            # if token:
            #     if token[1]:
            #         with open("templates/index.html", "r") as f:
            #             stringbody = f.read()
            #             stringbody = stringbody.replace('Guest', username)
            #         return make_response(stringbody)
        else: 
            # ERROR
            username = "guest"
        # print("fuck it, here's the whole database", mycursor.fetchall())
        # print('username displayed: ', user, 'auth_token received:', hashed_auth)
        connection.close()

    response =  Response(render_template('index.html', username=username))
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route('/direct_message/<recipient>')
def dm(recipient):
    username = get_username()
    return Response(render_template('direct_message.html', Recipient_Username=recipient))

@app.route('/register', methods=['POST'])
def giveRegister():
    username = request.form.get('username')
    password = request.form.get('password')
    print(username,password)
    same_password = request.form.get('password2')
    if password == same_password:
        print(password)
        connection, cursor = connect_to_database()
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        if (not table_exist('User',cursor)):
            print("table not existing")
            cursor.execute('CREATE Table IF NOT EXISTS User (username TEXT, password TEXT, auth_token TEXT, ID int PRIMARY KEY AUTO_INCREMENT)')
            connection.commit()
            print("table exists now? ", table_exist('User',cursor))
        exist = False
        cursor.execute("SELECT * FROM User")
        users = cursor.fetchall()
        for i in users:
            if i[0] == username:
                exist = True
        print(exist)
        if exist == False:
            cursor.execute('INSERT INTO User (username, password, auth_token) VALUES(%s,%s, %s)', (username, hashed_password, 'no auth'))
            connection.commit()
        connection.close()
    # response = Response(redirect(url_for('index')))
    # response.headers['X-Content-Type-Options'] = 'nosniff'
    # return response
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def giveLogin():
    response = make_response(redirect(url_for('index')))
    username = request.form.get('username')
    password = request.form.get('password')
    connection, cursor = connect_to_database()
    userTable = table_exist('User',cursor)
    tokenTable = table_exist('Token',cursor)
    if userTable and tokenTable:
        auth_token = secrets.token_hex(20)
        hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
        cursor.execute('SELECT * FROM User WHERE username = %s', (username,))
        exist = cursor.fetchall()
        if len(exist) != 0:
            exist = exist[0]
            hashed_password = exist[1]
            if bcrypt.checkpw(password.encode(), hashed_password.encode()):
                cursor.execute('INSERT INTO Token (auth_token, exist) VALUES(%s, %s)', (hashed_auth, True))
                update(hashed_auth, username,connection,cursor)
                response.set_cookie('auth_token', auth_token, max_age=7200)
                connection.commit()
                connection.close()
                return response
        connection.close()
        return response
    else:
        if not userTable:
            cursor.execute('CREATE Table IF NOT EXISTS User (username TEXT, password TEXT, auth_token TEXT, ID int PRIMARY KEY AUTO_INCREMENT)')
            connection.commit()
        if not tokenTable:
            cursor.execute('CREATE Table IF NOT EXISTS Token (auth_token TEXT, exist BOOLEAN)')
            connection.commit()
        auth_token = secrets.token_hex(20)
        hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
        cursor.execute('SELECT * FROM User WHERE username = %s', (username,))
        exist = cursor.fetchall()
        if len(exist) != 0:
            print(exist)
            exist = exist[0]
            hashed_password = exist['password']
            if bcrypt.checkpw(password.encode(), hashed_password):
                cursor.execute('INSERT INTO Token (auth_token, exist) VALUES(%s,%s)', (hashed_auth, True))
                update(hashed_auth, username,connection, cursor)
                response.set_cookie('auth_token', auth_token, max_age=7200)
                connection.close()
                return response
        connection.close()
        return response

@app.route('/logout', methods=['POST'])
def giveLogout():
    response = make_response(redirect(url_for('index')))
    if 'auth_token' in request.cookies:
        auth_token = request.cookies.get('auth_token')
        hashed_auth = hashlib.sha256(auth_token.encode()).hexdigest()
        connection, cursor = connect_to_database()
        update_token(hashed_auth,connection,cursor)
        connection.close()
        response.set_cookie('auth_token', '', expires=0)
    return response

@app.route('/createpost', methods=['POST'])
def createPostPolling():
    createPost(request.cookies.get('auth_token'), request.form.get('message'))
    response = make_response(redirect(url_for('index'))) #Return 200
    return response

def createPost(auth, message):
    #Create post should be called via html form
    inserted_id = -1
    print("Auth is: " + str(auth))
    print("Message is: " + str(message))
    message = message.replace("&", "&amp;") #Replaces & with html safe version
    message = message.replace(">", "&gt;") #Replaces > with html safe version
    message = message.replace("<", "&lt;") #Replaces < with html safe version
    message = message.replace("\"", "&quot;") #Replaces " with html safe version

    connection, cursor = connect_to_database()
    if not table_exist('Posts',cursor):
        script = 'CREATE Table if not exists Posts (username TEXT, message TEXT, ID int AUTO_INCREMENT, PRIMARY KEY (ID))'
        cursor.execute(script)
        connection.commit()

    # testCreate() #MUST REMOVE, JUST FOR TESTING!!!

    if auth is not None:
        hashed_auth = hashlib.sha256(auth.encode()).hexdigest()
        print("Hashed auth is: " + str(hashed_auth))
        if not table_exist("Token",cursor):
            cursor.execute('CREATE Table IF NOT EXISTS Token (auth_token TEXT, exist BOOLEAN)')
            connection.commit()
        script = 'SELECT * from Token where auth_token = %s'
        cursor.execute(script, (hashed_auth,))
        data = cursor.fetchall() #data[0] = auth_token data[1] = exist
        if len(data) != 0:
            data = data[0]
            print(data)
            if data[1] == True: #If auth token and proper auth token, create post
                script = 'Select username from User where auth_token = %s'
                cursor.execute(script, (hashed_auth,))
                username = cursor.fetchall()
                if len(username) != 0:
                    username = username[0]
                    script = 'INSERT into Posts (username, message) VALUES(%s, %s)'
                    username = username[0]
                    cursor.execute(script, (username, message))
                    connection.commit()
                    inserted_id = cursor.lastrowid
    connection.close()
    return inserted_id


@app.route('/like', methods=['POST'])
def createLike():
    #Create post should be called via html form
    auth = request.cookies.get('auth_token')
    id = request.form.get('id')
    connection, cursor = connect_to_database()
    if not table_exist('Likes',cursor):
        cursor.execute('CREATE Table IF NOT EXISTS Likes (ID int, username TEXT)')
        connection.commit()

    if auth is not None and id is not None:
        hashed_auth = hashlib.sha256(auth.encode()).hexdigest()
        script = 'SELECT * from Token where auth_token = %s'
        cursor.execute(script, (hashed_auth,))
        data = cursor.fetchall() #data[0] = auth_token data[1] = exist
        if len(data) != 0:
            data = data[1]
        if data[1] == True: #If auth token and proper auth token, create post
            script = 'Select username from User where auth_token = %s'
            cursor.execute(script, (hashed_auth,))
            username = cursor.fetchall()
            if len(username) != 0:
                username = username[0]
                script = 'SELECT * from Likes WHERE ID = %s'
                cursor.execute(script, (id,))
                data = cursor.fetchall()
                for line in data:
                    if line[1] == username[0]:
                        response = make_response(redirect(url_for('index'))) #Return 200
                        return response
                script = 'INSERT into Likes (ID, username) VALUES(%s, %s)'
                cursor.execute(script, (id, username[0],))
                connection.commit()
    connection.close()
    response = make_response(redirect(url_for('index'))) #Return 200
    return response

def testCreate():
    connection, cursor = connect_to_database()
    script = 'INSERT into Posts (username, message) VALUES(%s, %s)'
    cursor.execute(script, ("Gamer1", "Message1"))
    script = 'INSERT into Posts (username, message) VALUES(%s, %s)'
    cursor.execute(script, ("Gamer2", "Message2"))
    script = 'INSERT into Posts (username, message) VALUES(%s, %s)'
    cursor.execute(script, ("Gamer3", "Message3"))
    connection.commit()
    connection.close()

def fetchLikes(id, cursor):
    if not table_exist('Likes',cursor):
        return 0
    script = 'SELECT * from Likes WHERE ID = %s'
    cursor.execute(script, (id,))
    data = cursor.fetchall()
    likes = len(data)
    return likes

@app.route('/messages', methods=['GET'])
def readMessages():
    connection, cursor = connect_to_database()
    if not table_exist('Posts',cursor):
        script = 'CREATE Table if not exists Posts (username TEXT, message TEXT, ID int AUTO_INCREMENT, PRIMARY KEY (ID))'
        cursor.execute(script)
        connection.commit()
    script = 'SELECT username, message, id from Posts ORDER BY id DESC'
    cursor.execute(script)
    data = cursor.fetchall()
    result = []
    for line in data:
        result.append({"message": line[1], "username": line[0], "id": str(line[2]), "likes": str(fetchLikes(line[2],cursor))})
        # result.append({"message": line[1], "username": line[0], "id": line[3]})
    connection.close()
    return jsonify(result)

def update(auth_token, username, connection, cursor):
    cursor.execute('UPDATE User SET auth_token = %s WHERE username = %s', (auth_token, username))
    connection.commit

def update_token(auth_token, connection, cursor):
    cursor.execute('UPDATE Token SET exist = %s WHERE auth_token = %s', (False, auth_token))
    connection.commit 

def table_exist(name: str, cursor):
    cursor.execute("SHOW TABLES LIKE '" + name + "'")
    table = cursor.fetchall()
    if len(table) != 0:
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

@socketio.on('connect')
def handle_connect():
    print('socket connected')

@socketio.on('createpostrequest')
def ws_createpost(post):
    auth = post.get('auth_token')
    message = post.get('message')
    username = post.get('username')
    id = createPost(auth, message)
    emit('createpostresponse', {'message': message, 'username': username, 'id': id, 'likes': '0'}, broadcast=True)


# @sock.route('/websocket_index')
# def websocket_index(ws):
#     while True:
#         data = json.loads(ws.receive())
#         ws.send(data)

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=8080)

from flask import Flask, render_template, send_from_directory, make_response, redirect, url_for, request, jsonify, Response
from datetime import datetime, timedelta
import time as timer
# from flask_sock import Sock
from flask_socketio import SocketIO, emit
# from flask_apscheduler import APScheduler
import json
import mysql.connector
import bcrypt
import secrets
import hashlib
import os
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from time import time

last_breach = {}
clients = {}

def retrieve_remote_address():
    print(request.headers.get('X-Forwarded-For', request.remote_addr))
    return request.headers.get('X-Forwarded-For', request.remote_addr)

app = Flask(__name__)
# app.config['']
# sock = Sock(app)
limiter = Limiter(retrieve_remote_address, app=app,default_limits=["500 per 10 seconds"],storage_uri="memory://",strategy="fixed-window-elastic-expiry",)
appLimiter = limiter.shared_limit("0 per 30 seconds",scope="application", exempt_when=lambda: should_exempt(request.headers.get('X-Forwarded-For', request.remote_addr)))

socketio = SocketIO(app)
clients = {}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
config = {
    'host': 'oursql',
    'user': 'user', 
    'passwd': '31f58458f0cf8691fe88ab7e7720eea9089fd986',
    'database': 'mysql'
}

socketio = SocketIO(app)

@app.before_request
def before_request():
    address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if address in clients:
        clients[address].append(time())
    else:
        clients[address] = [time()]
    
def remove_before(requestTimeList, seconds):
    newTimeList = requestTimeList
    for requestTime in requestTimeList:
        if (time() - requestTime > seconds):
            newTimeList.remove(requestTime)
    return newTimeList


def should_exempt(client_ip):
    client = []
    if client_ip in clients:
        client = clients[client_ip]
        
    clients[client_ip] = remove_before(client.copy(), 10)
    if (len(clients[client_ip]) > 50):
        print("Client will be limited ", len(clients[client_ip]))
        return False
    if (client_ip in last_breach):
        if (time() - last_breach[client_ip] < 30):
            print("Client rate limited for 30 seconds after last post")
            return False
    print("Client not Limited. Total requests = ", len(clients[client_ip]))
    return True

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
            timer.sleep(3)
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
@appLimiter
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
@appLimiter
def dm(recipient):
    connection, cursor = connect_to_database()
    username = get_username()
    cookies = request.cookies
    auth = ''
    if 'auth_token' in cookies:
        auth = cookies['auth_token']
        hashed_auth = hashlib.sha256(auth.encode()).hexdigest()
        userTable = table_exist('User',cursor)
        tokenTable = table_exist('Token',cursor)
        if userTable:
            if tokenTable:
                cursor.execute('SELECT exist FROM Token WHERE auth_token = %s', (hashed_auth,))
                exist = cursor.fetchone()
                exist = exist[0]
                if exist:
                    cursor.execute('SELECT username FROM User WHERE auth_token = %s', (hashed_auth,))
                    username = cursor.fetchone()
                    username = username[0]
                    connection.close()
                    if username != recipient:
                        return Response(render_template('direct_message.html', Recipient_Username=recipient, username=username))
    response = make_response("Forbidden", 403)
    connection.close()
    return response
                


@app.route('/register', methods=['POST'])
@appLimiter
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
@appLimiter
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
            hashed_password = exist[1]
            if bcrypt.checkpw(password.encode(), hashed_password.encode()):
                cursor.execute('INSERT INTO Token (auth_token, exist) VALUES(%s,%s)', (hashed_auth, True))
                update(hashed_auth, username,connection, cursor)
                response.set_cookie('auth_token', auth_token, max_age=7200)
                connection.close()
                return response
        connection.close()
        return response

@app.route('/logout', methods=['POST'])
@appLimiter
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
@appLimiter
def createPostPolling():
    timer.sleep(int(request.form.get('delaypostinput')) * postUnitCalc(request.form.get('delaypostunit')))
    createPost(request.cookies.get('auth_token'), request.form.get('message'))
            #    request.form.get('delaypostinput'), request.form.get('delaypostunit'))
    response = make_response(redirect(url_for('index'))) #Return 200
    return response

def postUnitCalc(unit):
    unit_dict = {'sec': 1, 'min': 60, 'hr': 3600, 'day': 3600 * 24}
    return unit_dict[unit]

def calcPostTime(delay, unit):
    time_unit_dict = {'sec': timedelta(seconds=delay), 
                      'min': timedelta(minutes=delay),
                      'hr': timedelta(hours=delay),
                      'day': timedelta(days=delay)}
    return datetime.now() + time_unit_dict[unit]

def equalTime(datetime1, datetime2):
    return datetime1.second == datetime2.second \
        and datetime1.minute == datetime2.minute \
            and datetime1.hour == datetime2.hour \
                and datetime1.day == datetime2.day

@app.route('/remaining time', methods=['POST'])
def remaining_time():
    pass

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
        script = 'CREATE Table if not exists Posts (username TEXT, message TEXT, ID int AUTO_INCREMENT, image_link TEXT, user2 TEXT, PRIMARY KEY (ID))'
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
  
@socketio.on('createpostDM')
def createPostDM(message, recipient, user):
    print("TEST TWO")
    #Create post should be called via html form
    recipient_username = recipient
    print('Username:' + recipient_username)
    auth = request.cookies.get('auth_token')
    print("Auth is: " + str(auth))
    print("Message is: " + str(message))
    message = message.replace("&", "&amp;") #Replaces & with html safe version
    message = message.replace(">", "&gt;") #Replaces > with html safe version
    message = message.replace("<", "&lt;") #Replaces < with html safe version
    message = message.replace("\"", "&quot;") #Replaces " with html safe version

    connection, cursor = connect_to_database()
    if not table_exist('PostsDM',cursor):
        script = 'CREATE Table if not exists PostsDM (username TEXT, recipient_username TEXT, message TEXT, ID int AUTO_INCREMENT, PRIMARY KEY (ID))'
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
                    script = 'INSERT into PostsDM (username, recipient_username, message) VALUES(%s, %s, %s)'
                    username = username[0]
                    cursor.execute(script, (username, recipient_username, message))
                    connection.commit()
    connection.close()
    response = make_response(redirect('/direct_message/' + recipient_username)) #Return 200
    return response

@app.route('/like', methods=['POST'])
@appLimiter
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
            data = data[0]
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
                cursor.execute("SELECT * FROM Posts WHERE id = %s",(str(id),))
                record = cursor.fetchall()
                if len(record) != 0:
                    record = record[0]
                    username = record[0]
                    message = record[1]
                    likes = fetchLikes(id,cursor)
                    emit('updateLikes', {'id': id, 'likes': likes}, broadcast=True, namespace='/')
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
@appLimiter
def readMessages():
    connection, cursor = connect_to_database()
    if not table_exist('Posts',cursor):
        script = 'CREATE Table if not exists Posts (username TEXT, message TEXT, ID int AUTO_INCREMENT, image_link TEXT, user2 TEXT, PRIMARY KEY (ID))'
        cursor.execute(script)
        connection.commit()
    script = 'SELECT username, message, id, image_link, user2 from Posts ORDER BY id DESC'
    cursor.execute(script)
    data = cursor.fetchall()
    result = []
    for line in data:
        user = ""
        if line[4] != None:
            user = line[4]
        if line[3] == None:
            result.append({"message": line[1], "username": line[0], "id": str(line[2]), "likes": str(fetchLikes(line[2],cursor)), "image_link": "", "user2": user})
        else:
            result.append({"message": line[1], "username": line[0], "id": str(line[2]), "likes": str(fetchLikes(line[2],cursor)), "image_link": line[3], "user2": user})
        # result.append({"message": line[1], "username": line[0], "id": line[3]})
    connection.close()
    return jsonify(result)

@app.route('/DMmessages', methods=['GET'])
@appLimiter
def readDMMessages():
    username = request.args.get('username')
    recipient_username = request.args.get('Recipient_Username')
    connection, cursor = connect_to_database()
    if not table_exist('PostsDM', cursor):
        script = 'CREATE TABLE IF NOT EXISTS PostsDM (username TEXT, recipient_username TEXT, message TEXT, ID INT AUTO_INCREMENT, PRIMARY KEY (ID))'
        cursor.execute(script)
        connection.commit()

    script = 'SELECT username, recipient_username, message, id FROM PostsDM WHERE (username = %s AND recipient_username = %s) ORDER BY id DESC'
    cursor.execute(script, (username, recipient_username, recipient_username, username))
    data = cursor.fetchall()
    result = []
    for line in data:
        result.append({"message": line[2], "username": line[0], "recipient_username": line[1], "id": str(line[3]), "likes": str(fetchLikes(line[3], cursor))})
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

@app.route('/uploadPFP/<username>', methods=['POST'])
@appLimiter
def uploadPFP(username):
    connection, cursor = connect_to_database()
    if username == 'guest' or username == 'Guest':
        return make_response("Forbidden", 403)
    auth = request.cookies.get('auth_token')
    if not auth:
        return make_response("Forbidden", 403)
    hashed_auth = hashlib.sha256(auth.encode()).hexdigest()
    if not table_exist("Token",cursor):
            cursor.execute('CREATE Table IF NOT EXISTS Token (auth_token TEXT, exist BOOLEAN)')
            connection.commit()
    script = 'SELECT * from Token where auth_token = %s'
    cursor.execute(script, (hashed_auth,))
    data = cursor.fetchall() #data[0] = auth_token data[1] = exist
    if len(data) != 0:
        data = data[0]
        print('HERE IS:')
        print(data)
        if data[1] == True: #If auth token and proper auth token, create post
            print('got to data[1]')
            script = 'Select username from User where auth_token = %s'
            cursor.execute(script, (hashed_auth,))
            user = cursor.fetchall()
            if len(user) != 0:
                print('username exist')
                username2 = user[0][0]
                print(username2)
                print(username)
                if username == username2:
                    print('username equals auth token username')
                    file = request.files['file']
                    print(file.filename)
                    print('got here')
                    if file is not None and '.' in file.filename:
                        print('file exist')
                        fileName = secure_filename(file.filename)
                        fileExtension = fileName.rsplit('.', 1)[1].lower()
                        if fileExtension in ALLOWED_EXTENSIONS:
                            print('allowed?')
                            if not table_exist('ProfilePic', cursor):
                                script = 'CREATE Table if not exists ProfilePic (username TEXT, ID int AUTO_INCREMENT, image_link TEXT, PRIMARY KEY (ID))'
                                cursor.execute(script)
                                connection.commit()
                            script = 'SELECT * FROM ProfilePic WHERE username = %s'
                            cursor.execute(script, (username,))
                            data = cursor.fetchone()
                            connection.commit()
                            if not data:
                                script = 'SELECT * FROM ProfilePic ORDER BY ID DESC LIMIT 1'
                                cursor.execute(script)
                                id = cursor.fetchone()
                                print(id)
                                if id == None:
                                    fileName = "PFP" + str(1) + "." + fileExtension
                                else:
                                    id = id[1]
                                    fileName = "PFP" + str(id + 1) + "." + fileExtension
                                cursor.execute('INSERT INTO ProfilePic (username, image_link) VALUES(%s,%s)', (username, fileName))
                                connection.commit()
                            if data:
                                id = data[1]
                                fileName = "PFP" + str(id) + "." + fileExtension
                            file.save('/code/public/' + fileName)
                            script = 'SELECT * FROM ProfilePic WHERE username = %s'
                            cursor.execute(script, (username,))
                            data = cursor.fetchone()
                            connection.commit()
                            print('MOrE test')
                            print(fileName)
                            print(username)
                            emit('updateProfilePicture', {'image_link': fileName, 'username': username}, broadcast=True, namespace='/')

    print('Here')
    print(username)
    cursor.close()
    connection.close()
    return redirect("/", code=302)

@app.route('/upload', methods=['POST'])
@appLimiter
def uploadFile():
    file = request.files['file']
    print(file.filename)
    if file is not None and '.' in file.filename:
        fileName = secure_filename(file.filename)
        fileExtension = fileName.rsplit('.', 1)[1].lower()
        if fileExtension in ALLOWED_EXTENSIONS:
            connection, cursor = connect_to_database()
            auth = request.cookies.get('auth_token')
            id = request.form.get('id')
            username = request.form.get('username')
            fileName = "Post" + str(id) + "." + fileExtension
            script = 'UPDATE Posts SET image_link = %s WHERE id = %s'
            cursor.execute(script, (fileName, id))
            script = 'UPDATE Posts SET user2 = %s WHERE id = %s'
            cursor.execute(script, (username, id))
            connection.commit()
            file.save('/code/public/' + fileName)
            cursor.execute("SELECT * FROM Posts WHERE id = %s",(str(id),))
            record = cursor.fetchall()
            if len(record) != 0:
                record = record[0]
                message = record[1]
                likes = fetchLikes(id,cursor)
                emit('updatePost', {'message': message, 'username': username, 'id': id, 'likes': likes, 'image_link': fileName}, broadcast=True, namespace='/')
            cursor.close()
            connection.close()

    return redirect("/", code=302)

@app.route('/userUploads/<filename>')
@appLimiter
def giveUserFile(filename):
    fileName = secure_filename(filename)
    print("The filename is: " + fileName)
    return send_from_directory("public", fileName)

@app.route('/PFPUploads/<filename>')
@appLimiter
def givePFP(filename):
    fileName = secure_filename(filename)
    print("The filename is: " + fileName)
    return send_from_directory("public", fileName)

@app.route('/css/<css>') #Returns any file from css directory
@appLimiter
def giveCSS(css):
    return send_from_directory('css', css)

@app.route('/js/<js>') #Returns any file from js directory
@appLimiter
def giveJS(js):
    return send_from_directory('js', js)

@app.route('/images/<images>') #Returns any file from images directory
@appLimiter
def giveImage(images):
    return send_from_directory('images', images)

@socketio.on('connect')
@appLimiter
def handle_connect():
    print('socket connected')

@socketio.on('createpostrequest')
def ws_createpost(post):
    auth = post.get('auth_token')
    message = post.get('message')
    username = post.get('username')
    connection, cursor = connect_to_database()
    delay = post.get('delay')
    if delay is None or delay == '':
        delay = 0
    time_remaining = int(delay) * postUnitCalc(post.get('delay_unit'))
    print('time_remaining', time_remaining)

    if not table_exist('Delayed_Posts', cursor):
        script = 'CREATE Table if not exists Delayed_Posts (ID int AUTO_INCREMENT, time_remaining int, PRIMARY KEY (ID))'
        cursor.execute(script)
        connection.commit()

    script = 'INSERT INTO Delayed_Posts (time_remaining) VALUES (%s)'
    cursor.execute(script, (time_remaining,))
    connection.commit()
    script = 'SELECT ID From Delayed_Posts ORDER BY ID DESC LIMIT 1'
    cursor.execute(script)
    time_remaining_id = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    emit('timeremainingid', {'id': time_remaining_id})
    # print('post delay', post.get('delay') * postUnitCalc(post.get('delay_unit')))
    timer.sleep(int(delay) * postUnitCalc(post.get('delay_unit')))
    id = createPost(auth, message)
    emit('createpostresponse', {'message': message, 'username': username, 'id': id, 'likes': '0', 'image_link': "", 'user2': ""}, broadcast=True)

@app.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if address in last_breach:
        if (time() - last_breach[address] > 30):
            last_breach[address] = time()
    else:
        last_breach[address] = time()
    clients[address] = []
    return "ratelimit exceeded! Too many requests. Please wait 30 seconds", 429
@app.route('/time_remaining')
def send_time_remaining():
    time_remaining_id = int(request.cookies.get('time_remaining_id', '0'))
    connection, cursor = connect_to_database()
    if not table_exist('Delayed_Posts', cursor):
        script = 'CREATE Table if not exists Delayed_Posts (ID int AUTO_INCREMENT, time_remaining int, PRIMARY KEY (ID))'
        cursor.execute(script)
        connection.commit()
        return jsonify({'time_remaining': 0})
    script = 'SELECT time_remaining FROM Delayed_Posts WHERE ID = ' + str(time_remaining_id) + ' ORDER BY ID DESC'
    cursor.execute(script)
    data = cursor.fetchone()[0]
    if data > 0:
        data -= 1
    # script = 'INSERT INTO Delayed_Posts (time_remaining) VALUES (%s)'
    script = 'UPDATE Delayed_Posts SET time_remaining = %s WHERE ID = %s'
    cursor.execute(script, (data,time_remaining_id))
    connection.commit()
    return jsonify({'time_remaining':data})

# @sock.route('/websocket_index')
# def websocket_index(ws):
#     while True:
#         data = json.loads(ws.receive())
#         ws.send(data)

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=8080)
    socketio.run(app)
    

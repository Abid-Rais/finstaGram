from flask import Flask, render_template, request, session, url_for, redirect, send_file
import os
import pymysql.cursors
import hashlib
import mysql.connector
from mysql.connector import Error
from datetime import date, time, datetime

app = Flask(__name__)
app.secret_key = 'some key that you will never guess'
IMAGES_DIR = os.path.join(os.getcwd(), "images")

conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='password',
                       db='finstaGramDB',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/login')
# def login():
#     return render_template('login.html')

# @app.route('/register')
# def register():
#     return render_template('register.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    data = cursor.fetchone()
    cursor.close()
    error = None
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or username'
        return render_template('index.html', error=error)

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    username = request.form['username']
    password = request.form['password']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    bio = request.form['bio']

    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, username)
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('index.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, firstName, lastName, bio))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home', methods=['GET'])
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM Photo ORDER BY postingDate DESC'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, images=data)

@app.route("/images/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

@app.route("/upload", methods=['GET'])
def upload():
    return render_template("upload.html")

@app.route('/postPhoto', methods=['POST', 'GET'])
def postPhoto():
    if request.files and request.method =='POST':
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)

        username = session['username']
        caption = request.form['caption']

        query = "INSERT INTO Photo (photoPoster, photoPath, postingdate, caption) VALUES (%s, %s, %s, %s)"
        with conn.cursor() as cursor:
            cursor.execute(query, (username, image_name, datetime.now(), caption))
            conn.commit()
            cursor.close()
        message = "Image has been successfully uploaded."
        return render_template("postPhoto.html", message=message)
    return render_template("postPhoto.html")

# @app.route('/likePhoto', methods=['POST'])
# def likePhoto(): 
    
#     query = 'UPDATE Photo SET like = like + 1 WHERE photoID = %s'
#     with conn.cursor() as cursor: 
#         cursor.execute(query, photoID)
#         conn.commit()
#     return render_template('home.html', username=user, images=data)

# @app.route('/commentPhoto', methods=['POST'])
# def commentPhoto(): 
#     pass

# @app.route('/showComment', methods=['GET'])
# def showComment(): 
#     pass

@app.route('/selectUser', methods=["GET"])
def selectUser():
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM Person'
    cursor.execute(query)
    user_data = cursor.fetchall()
    cursor.close()
    return render_template('selectUser.html', user_list=user_data)

@app.route('/showPosts', methods=['GET','POST'])
def showPosts():
    print("IN HERE")
    user = request.form["selected_person"]
    print("User:",user)
    cursor = conn.cursor()
    query = 'SELECT * FROM photo WHERE photoPoster = %s ORDER BY postingdate DESC'
    cursor.execute(query, user)
    data = cursor.fetchall()
    cursor.close()
    return render_template('showPosts.html', username=user, images=data)

# @app.route('/showPosts', methods=["GET", "POST"])
# def showPosts():
#     poster = request.args['poster']
#     cursor = conn.cursor();
#     query = 'SELECT photoID, postingdate FROM photo WHERE photoPoster = %s ORDER BY postingdate DESC'
#     cursor.execute(query, poster)
#     data = cursor.fetchall()
#     cursor.close()
#     return render_template('show_posts.html', poster_name=poster, posts=data)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run('127.0.0.1', 5000, debug=True)

SALT = 'cs3083'



from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import mysql.connector
from mysql.connector import Error
from datetime import date

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='password',
                       db='finstaGramDB',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

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


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT photoPoster, postingdate, caption FROM Photo WHERE photoPoster = %s ORDER BY postingDate DESC'
    cursor.execute(query, (user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, posts=data)

def convertToBinaryData(filename):
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def insertBlob(photoID, photoPoster, biodata, photo_src, allFollowers, caption):
    try:
        print("Inserting BLOB into photo table")
        cursor = conn.cursor()
        sql_insert_blob_query = """ INSERT INTO photo
                            (photoID, photoPoster, postingdate, biodata, photo, allFollowers, caption) VALUES
        (%s, %s, %s, %s)"""
        photo = convertToBinaryData(photo_src)
        file = convertToBinaryData(biodata)

        insert_blob_tuple = (photoID, photoPoster, date.today(), file, photo, allFollowers, caption)
        result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
        connection.commit()
        print("Image and file inserted successfully as a BLOB into photo table", result)
    except mysql.connector.Error as error:
        print("Failed inserting BLOB data into MySQL table {}".format(error))
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

@app.route('/post_photo', methods=['GET', 'POST'])
def post_photo():
    username = session['username']

    photoID = request.form['photoID']
    biodata = request.form['biodata']
    photo_src = request.form['photo_src']
    allFollowers = request.form['allFollowers']
    caption = request.form['caption']

    insertBlob(photoID, username, biodata, photo_src, allFollowers, caption)
    # cursor = conn.cursor();
    # blog = request.form['blog']
    # query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
    # cursor.execute(query, (blog, username))
    # conn.commit()
    # cursor.close()
    return redirect(url_for('home'))

def write_file(data, filename):
    #Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)

def readBLOB():
    print("Reading BLOB data from photo table")
    try:
        cursor = connection.cursor()
        sql_fetch_blob_query = """SELECT photo from Photo WHERE photoPoster = %s"""
        cursor.execute(sql_fetch_blob_query, )

@app.route('/friend_groups')
def friend_groups():
    cursor = conn.cursor();



@app.route('/select_blogger')
def select_blogger():
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM Person'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT photoID, postingdate FROM photo WHERE photoPoster = %s ORDER BY postingdate DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)

SALT = 'cs3083'



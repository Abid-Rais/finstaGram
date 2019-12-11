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
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM Photo ORDER BY postingDate DESC'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, images=data)

@app.route('/viewInfo/<photoID>', methods=['GET'])
def viewInfo(photoID):
    cursor = conn.cursor()
    query = 'SELECT * FROM Photo WHERE photoID = %s'
    cursor.execute(query, photoID)
    image_data = cursor.fetchone()
    query = 'SELECT DISTINCT firstName, lastName FROM Person INNER JOIN Photo ON username = photoPoster WHERE username= %s'
    cursor.execute(query, image_data['photoPoster'])
    person_data = cursor.fetchone()
    query = 'SELECT DISTINCT commentStr, ts, username FROM comment INNER JOIN Photo WHERE comment.photoID = %s'
    cursor.execute(query, image_data['photoID'])
    comment_data = cursor.fetchall()
    cursor.close()
    return render_template('viewInfo.html', image=image_data, person=person_data, comments=comment_data)

@app.route("/images/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

@app.route('/postPhoto', methods=['POST', 'GET'])
def postPhoto():
    if request.files and request.method =='POST':
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)

        username = session['username']
        caption = request.form['caption']

        visible = True
        if request.form['allFollowers'] == "no":
            visible = False

        query = "INSERT INTO Photo (photoPoster, filepath, postingdate, caption, allFollowers) VALUES (%s, %s, %s, %s, %s)"
        cursor = conn.cursor()
        cursor.execute(query, (username, image_name, datetime.now(), caption, visible))
        conn.commit()
        cursor.close()
        message = "Image has been successfully uploaded."
        return render_template("postPhoto.html", message=message)
    return render_template("postPhoto.html")

@app.route('/commentPhoto', methods=['GET','POST'])
def commentPhoto(): 
    comment = request.form['comment']
    photoID = request.form['photoID']
    username = session['username']
    photoPoster = request.form['photoPoster']
    query = "INSERT INTO comment (commentStr, ts, photoID, username, poster) VALUES (%s, %s, %s, %s, %s)"
    cursor = conn.cursor()
    cursor.execute(query, (comment, datetime.now(), photoID, username, photoPoster))
    conn.commit()

    query = 'SELECT * FROM Photo ORDER BY postingDate DESC'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, images=data)

@app.route('/selectUser')
def selectUser():
    return render_template('selectUser.html')

@app.route('/showPosts', methods=['GET','POST'])
def showPosts():
    user = request.form["selected_person"]
    cursor = conn.cursor()
    query = 'SELECT * FROM photo WHERE photoPoster = %s ORDER BY postingdate DESC'
    cursor.execute(query, user)
    images_data = cursor.fetchall()
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, user)
    person_data = cursor.fetchone()
    cursor.close()
    return render_template('showPosts.html', person=person_data, images=images_data)

@app.route('/manageFollows')
def manageFollows(): 
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT DISTINCT username_follower FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor.execute(query, username)
    user_data = cursor.fetchall()
    cursor.close()
    return render_template('manageFollows.html', users=user_data)

@app.route('/requestFollow', methods=['GET', 'POST'])
def requestFollow(): 
    username = session['username']
    followed = request.form['followed']
    cursor = conn.cursor()
    query = 'INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, 0)'
    cursor.execute(query, (followed, username))
    conn.commit()
    
    query = 'SELECT DISTINCT username_followed FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor.execute(query, username)
    user_data = cursor.fetchall()
    cursor.close()
    return render_template('manageFollows.html', users=user_data)

@app.route('/acceptFollow', methods=['GET', 'POST'])
def acceptFollow(): 
    username = session['username']
    follower = request.form['follower']
    cursor = conn.cursor()
    query = 'UPDATE Follow SET followstatus = 1 WHERE username_follower = %s AND username_followed = %s'
    cursor.execute(query, (follower, username))
    conn.commit()

    query = 'SELECT DISTINCT username_followed FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor.execute(query, username)
    user_data = cursor.fetchall()
    cursor.close()
    print(4)
    return render_template('manageFollows.html', users=user_data)

@app.route('/declineFollow', methods=['GET', 'POST'])
def declineFollow():
    username = session['username']
    follower = request.form['follower']
    cursor = conn.cursor()
    query = 'DELETE FROM Follow WHERE username_follower = %s AND username_followed = %s'
    cursor.execute(query, (follower, username))
    conn.commit()

    query = 'SELECT DISTINCT username_followed FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor.execute(query, username)
    user_data = cursor.fetchall()
    cursor.close()
    return render_template('manageFollows.html', users=user_data)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run('127.0.0.1', 5000, debug=True)

SALT = 'cs3083'



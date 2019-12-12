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

displayAllowedImagesQuery = "SELECT * FROM photo JOIN person ON ( username = photoPoster) \
            WHERE photoID IN( \
            SELECT DISTINCT photoID \
            FROM photo \
            WHERE photoPoster = %s OR photoID IN( \
                                        SELECT DISTINCT photoID \
                                        FROM photo JOIN follow ON (photoPoster = username_followed) \
                                        WHERE (allFollowers = True AND username_follower = %s AND followstatus = True) \
                                        OR photoID IN( SELECT DISTINCT photoID \
                                                    FROM friendgroup AS F \
                                                    JOIN belongto As B ON F.groupName = B.groupName AND F.groupOwner = B.owner_username \
                                                    JOIN sharedwith AS S ON F.groupName = S.groupName AND F.groupOwner = S.groupOwner \
                                                    WHERE member_username = %s)))"

@app.route('/')
def index():
    return render_template('index.html')

# Login Authorization
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # Form Requests
    username = request.form['username']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # mySQL Query Execute
    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    data = cursor.fetchone()
    cursor.close()
    error = None

    if(data): #If user is registered
        session['username'] = username
        return redirect(url_for('home'))
    else: #If user is not registered
        error = 'Invalid login or username'
        return render_template('index.html', error=error)

# Register Authorization
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #Form Requests
    username = request.form['username']
    password = request.form['password']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    bio = request.form['bio']

    # mySQL Query Execute
    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, username)
    data = cursor.fetchone()
    error = None

    if(data): #If user already exists
        error = "This user already exists"
        return render_template('index.html', error = error)
    else: #If user is new
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, password, firstName, lastName, bio))
        conn.commit()
        cursor.close()
        return render_template('index.html')

#Homepage for user, displays all photos visible to user
@app.route('/home', methods=['GET']) 
def home():
    username = session['username']
    cursor = conn.cursor()
    query = displayAllowedImagesQuery
    cursor.execute(query, (username, username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, images=data)

# Request to see Additional Info for a Photo
@app.route('/viewInfo/<photoID>', methods=['GET'])
def viewInfo(photoID):
    cursor = conn.cursor()

    # Fetch image_data
    query = 'SELECT * FROM Photo WHERE photoID = %s'
    cursor.execute(query, photoID)
    image_data = cursor.fetchone()

    # Fetch person_data
    query = 'SELECT DISTINCT firstName, lastName FROM Person INNER JOIN Photo ON username = photoPoster WHERE username= %s'
    cursor.execute(query, image_data['photoPoster'])
    person_data = cursor.fetchone()

    # Fetch comments_data
    query = 'SELECT DISTINCT commentStr, ts, username FROM comment INNER JOIN Photo WHERE comment.photoID = %s'
    cursor.execute(query, photoID)
    comment_data = cursor.fetchall()

    # Fetch likes_data
    query = 'SELECT username, rating FROM Likes WHERE photoID = %s'
    cursor.execute(query, photoID)
    likes_data = cursor.fetchall()

    # Fetch tagged_data
    query = 'SELECT username FROM Tagged WHERE photoID = %s AND tagstatus = 1'
    cursor.execute(query, photoID)
    tagged_data = cursor.fetchall()

    cursor.close()
    return render_template('viewInfo.html', image=image_data, person=person_data, comments=comment_data, likes=likes_data, tagged=tagged_data)

# Request Image
@app.route("/images/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

# Post a Photo
@app.route('/postPhoto', methods=['POST', 'GET'])
def postPhoto():
    # Form Requests
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

        # mySQL Query Execute
        query = "INSERT INTO Photo (photoPoster, filepath, postingdate, caption, allFollowers) VALUES (%s, %s, %s, %s, %s)"
        cursor = conn.cursor()
        cursor.execute(query, (username, image_name, datetime.now(), caption, visible))
        conn.commit()
        cursor.close()
        message = "Image has been successfully uploaded."
        return render_template("postPhoto.html", message=message)
    return render_template("postPhoto.html")

@app.route('/requestFollow', methods=['GET', 'POST'])
def requestFollow(): 
    # Form Requests
    username = session['username']
    followed = request.form['followed']
    cursor = conn.cursor()

    # mySQL Query Execute
    query = 'INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, 0)'
    cursor.execute(query, (followed, username))
    conn.commit()
    
    # Refresh Homepage
    query = 'SELECT DISTINCT username_followed FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor.execute(query, username)
    user_data = cursor.fetchall()
    cursor.close()
    return render_template('manageFollows.html', users=user_data)

# List all Users who have Requested Access
@app.route('/manageFollows')
def manageFollows(): 
    # Form Requests
    username = session['username']
    
    # mySQL Query Execute
    query = 'SELECT DISTINCT username_follower FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor = conn.cursor()
    cursor.execute(query, username)
    user_data = cursor.fetchall()
    cursor.close()
    return render_template('manageFollows.html', users=user_data)

# Accept a Follow Request
@app.route('/acceptFollow', methods=['GET', 'POST'])
def acceptFollow(): 
    # Form Requests
    username = session['username']
    follower = request.form['follower']

    # mySQL Query Execute
    query = 'UPDATE Follow SET followstatus = 1 WHERE username_follower = %s AND username_followed = %s'
    cursor = conn.cursor()
    cursor.execute(query, (follower, username))
    conn.commit()

    # Refresh Homepage
    query = 'SELECT DISTINCT username_follower FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor.execute(query, username)
    user_data = cursor.fetchall()
    cursor.close()
    return render_template('manageFollows.html', users=user_data)

# Decline a Follow Request
@app.route('/declineFollow', methods=['GET', 'POST'])
def declineFollow():
    # Form Requests
    username = session['username']
    follower = request.form['follower']
    
    # mySQL Query Execute
    query = 'DELETE FROM Follow WHERE username_follower = %s AND username_followed = %s'
    cursor = conn.cursor()
    cursor.execute(query, (follower, username))
    conn.commit()

    # Refresh Homepage
    query = 'SELECT DISTINCT username_follower FROM Follow WHERE username_followed = %s AND followstatus = 0'
    cursor.execute(query, username)
    user_data = cursor.fetchall()
    cursor.close()
    return render_template('manageFollows.html', users=user_data)

 # Comment on a Photo
@app.route('/commentPhoto', methods=['GET','POST'])
def commentPhoto(): 
    # Form Requests
    comment = request.form['comment']
    photoID = request.form['photoID']
    username = session['username']
    photoPoster = request.form['photoPoster']

    # mySQL Query Execute
    query = "INSERT INTO Comment (commentStr, ts, photoID, username, poster) VALUES (%s, %s, %s, %s, %s)"
    cursor = conn.cursor()
    cursor.execute(query, (comment, datetime.now(), photoID, username, photoPoster))
    conn.commit()

    # Refresh homepage
    query = displayAllowedImagesQuery
    cursor.execute(query, (username, username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, images=data)

# Like a Photo
@app.route('/likePhoto', methods=['GET', 'POST'])
def likePhoto(): 
    # Form Requests
    username = session['username']
    photoID = request.form['photoID']
    rating = (int(request.form['rating']) - 1 ) % 10 +1
    cursor = conn.cursor()

    try: #If a user likes an image for the first time
        query = 'INSERT INTO Likes (username, photoID, liketime, rating) VALUES (%s, %s, %s, %s)'
        cursor.execute(query, (username, photoID, datetime.now(), str(rating)))
        conn.commit()
    except: #If a user likes an image again after the first time
        query = 'UPDATE Likes SET rating = %s WHERE username = %s and photoID = %s'
        cursor.execute(query, (str(rating), username, photoID))
        conn.commit()

    # Refresh Homepage
    query = displayAllowedImagesQuery
    cursor.execute(query, (username, username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, images=data)

# Search a User
@app.route('/selectUser')
def selectUser():
    return render_template('selectUser.html')

# Display Posts and Information for a User
@app.route('/showPosts', methods=['GET','POST'])
def showPosts():
    # Form Requests
    curr_user = session['username']
    username = request.form['selected_person']
    
    # mySQL Query Execute
    query = displayAllowedImagesQuery   
    cursor = conn.cursor() 
    cursor.execute(query, (username, curr_user, curr_user))
    images_data = cursor.fetchall()
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, username)
    person_data = cursor.fetchone()
    cursor.close()
    return render_template('showPosts.html', person=person_data, images=images_data)

# Logout
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run('127.0.0.1', 5000, debug=True)

SALT = 'cs3083'



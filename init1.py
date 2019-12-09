#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib

SALT = 'cs3083'

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='',
                       db='Finnstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashed_password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    first = request.form['firstname']
    last = request.form['lastname']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed_password, first, last, ''))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/loginufool')
def loginufool():
    return render_template('loginufool.html')

@app.route('/home')
def home():
        #check that user is logged in
    try:
        user = session['username']
    except KeyError:
        return redirect(url_for('loginufool'))
        #should throw exception if username not found
    
    cursor = conn.cursor()
    
    query = 'SELECT * FROM photo WHERE photoposter = %s ORDER BY postingdate DESC'
    cursor.execute(query, (user))
    data = cursor.fetchall()
    
    query = 'SELECT groupName FROM belongTo WHERE member_username = %s'
    cursor.execute(query, (user))
    gr = cursor.fetchall()
    
    cursor.close()
    return render_template('home.html', username=user, posts=data, groups = gr)
    
@app.route('/moreinfo/<string:photoid>', methods=['GET','POST'])
def moreinfo(photoid):

    #check that user is logged in
    try:
        username = session['username']
    except KeyError:
        return redirect(url_for('loginufool'))
        #should throw exception if username not found

    cursor = conn.cursor();
    
    query = '''SELECT photoid
                FROM photo
                WHERE 
                photoid = %s AND (AllFollowers = True AND photoPoster IN (SELECT username_followed FROM follow WHERE username_follower = %s AND followstatus = True))
                OR 
                photoid IN (SELECT photoid FROM SharedWith NATURAL JOIN BelongTo WHERE member_username = %s)
                OR photoPoster = %s
                ORDER BY photoID DESC''' #makes sure the photo is visible
    cursor.execute(query, (photoid, username, username, username))
    data = cursor.fetchall()
    error = None
    
    if(data):
        query = 'SELECT * FROM photo WHERE photoid = %s'
        cursor.execute(query, (photoid));
        photo = cursor.fetchall()

        query = 'SELECT DISTINCT firstName, lastName FROM person WHERE username IN (SELECT photoPoster AS username FROM photo WHERE photoID = %s)'
        cursor.execute(query, (photoid));
        postername = cursor.fetchall()
    
        query = 'SELECT username FROM tagged WHERE photoID = %s AND tagstatus = 1'
        cursor.execute(query, (photoid));
        t = cursor.fetchall();
    
        query = 'SELECT username, rating FROM likes WHERE photoID = %s'
        cursor.execute(query, (photoid));
        l = cursor.fetchall();
    
        query = 'SELECT * FROM tagged WHERE photoID = %s AND username=%s AND tagStatus = 0'
        cursor.execute(query, (photoid, username))
        tagReq = cursor.fetchall();
        
        cursor.close()
        return render_template('moreinfo.html', post = photo, name = postername, tagged = t, liked = l, tagReq = tagReq)
    else:
        error = "Quit snoopin' around LOSER this photo ain't visible to ya"
        return render_template('moreinfo.html', error = error)
        
@app.route('/addtag/<string:photoid>', methods=['GET','POST'])
def addtag(photoid):
    username = session['username']
    cursor = conn.cursor()
    
    tuser = request.form['tag']
    status = "0"
    
    if(username == tuser):
        status = "1"
    else:
        status = "0"
    
    query = 'SELECT * FROM tagged WHERE username = %s AND photoID = %s';
    cursor.execute(query, (tuser, photoid))
    data = cursor.fetchall()
    error = None
    
    if (data):
        error = "already tagged"
        cursor.close()
        return redirect(url_for('moreinfo', photoid = photoid))
    else:
        query = 'INSERT INTO tagged VALUES(%s,%s,%s)'
        cursor.execute(query,(tuser, photoid, status));
        conn.commit()
        cursor.close()
        return redirect(url_for('moreinfo', photoid = photoid))
    
@app.route('/acceptTag/<string:photoid>', methods=['GET','POST'])
def acceptTag(photoid):
    username = session['username']
    cursor = conn.cursor()
    
    query = 'UPDATE tagged SET tagStatus = 1 WHERE username = %s AND photoID = %s'
    cursor.execute(query, (username, photoid));
    
    conn.commit()
    cursor.close()
    return redirect(url_for('moreinfo', photoid = photoid))
    
@app.route('/declineTag/<string:photoid>', methods=['GET','POST'])
def declineTag(photoid):
    username = session['username']
    cursor = conn.cursor()
    
    query = 'DELETE FROM tagged WHERE username = %s AND photoID = %s'
    cursor.execute(query, (username, photoid));
    
    conn.commit()
    cursor.close()
    return redirect(url_for('moreinfo', photoid = photoid))

@app.route('/follows', methods=['GET','POST'])
def follows():
    #check that user is logged in
    try:
        username = session['username']
    except KeyError:
        return redirect(url_for('loginufool'))
        #should throw exception if username not found
        
    cursor = conn.cursor();
    
    query = 'SELECT * FROM follow WHERE username_followed = %s AND followStatus = False'
    cursor.execute(query, username)
    data = cursor.fetchall()
    
    error = None
    cursor.close()
    return render_template('follows.html', requests = data, error=error)
    
@app.route('/sendfollow', methods=['GET', 'POST'])
def sendfollow():
    username = session['username']
    cursor = conn.cursor()
    fuser = request.form['fuser']
    query = 'SELECT * FROM follow WHERE username_followed = %s AND username_follower = %s';
    cursor.execute(query, (fuser, username))
    data = cursor.fetchall()
    error = None

    if(data):
        error = "Follow request already sent"
        cursor.close()
        return  redirect(url_for('follows'))
    else:
        query = 'INSERT INTO follow VALUES(%s, %s, False)'
        cursor.execute(query, (fuser, username))
        conn.commit()
        cursor.close()
        return redirect(url_for('follows'))

@app.route('/acceptfollow/<string:follower>',  methods=['GET','POST'])
def acceptfollow(follower):
    username = session['username']
    cursor = conn.cursor()
    
    query = 'UPDATE follow SET followStatus = True WHERE username_followed = %s AND username_follower = %s'
    cursor.execute(query, (username, follower));
    
    conn.commit()
    cursor.close()    
    return redirect(url_for('follows'))

@app.route('/declinefollow/<string:follower>',  methods=['GET','POST'])
def declinefollow(follower):
    username = session['username']
    cursor = conn.cursor();

    query = 'DELETE FROM follow WHERE username_followed = %s AND username_follower = %s'
    cursor.execute(query, (username, follower));

    conn.commit()
    cursor.close()        
    return redirect(url_for('follows'))
    
        
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    photo = request.form['photo']
    caption = request.form['caption']
    allfollow = request.form['allfollowers']
    friendgs = request.form['friendgs']
    if allfollow == '1':
        alf = 1
    else:
        alf = 0

    friendgroups = friendgs.split(',')
    i = 0;
    while(i < len(friendgroups)):
        friendgroups[i] = friendgroups[i].strip();
        i += 1;
    
    print(friendgroups)
    
    query = 'INSERT INTO photo (postingdate, filepath,allFollowers,caption,photoPoster) VALUES(NOW(), %s, %s, %s, %s)'
    cursor.execute(query, (photo, alf, caption, username))
    
    query = "SELECT photoID FROM Photo where photoposter = '" + username + "' ORDER BY photoID DESC LIMIT 1;"
    cursor.execute(query)
    photoid = cursor.fetchall()

    i = 0;
    
    while(i < len(friendgroups)):
        query = "SELECT DISTINCT owner_username FROM BelongTo WHERE groupName = %s AND member_username = %s;"
        cursor.execute(query, (friendgroups[i], username))
        groupowner = cursor.fetchall()
        
        print ("groupowner: ")
        print(groupowner)
        
        for g in groupowner:
            query = "INSERT INTO sharedwith VALUES (%s, %s, %s)"
            for p in photoid:
                cursor.execute(query, (g['owner_username'], friendgroups[i], p['photoID']))
                
        i+=1
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/visible')
def visible():
    #check that user is logged in
    try:
        username = session['username']
    except KeyError:
        error = "You must be logged in to view this page."
        return render_template('visible.html', error=error)
        #should throw exception if username not found
    
    cursor = conn.cursor();
    query = '''SELECT *
                FROM photo
                WHERE 
                (AllFollowers = 1 AND photoPoster IN (SELECT username_followed FROM follow WHERE username_follower = %s AND followstatus = True))
                OR 
                photoid IN (SELECT photoid FROM SharedWith NATURAL JOIN BelongTo WHERE member_username = %s)
                ORDER BY photoID DESC'''
    cursor.execute(query, (username, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('visible.html', visibles=data)


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

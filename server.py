from flask import Flask, render_template, session, redirect, request, flash
from mysqlconnection import MySQLConnector
import re
import bcrypt

app = Flask(__name__)
app.secret_key = "keepitsecret"
mysql = MySQLConnector(app, 'the_wall')
email_regex = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.+_-]+\.[a-zA-Z]+$')

@app.route('/')
def index():
	return render_template("index.html")

@app.route('/newUser', methods=['POST'])
def newUser():
	valid = True
	print request.form
	#validate first/last names
	if len(request.form['first_name']) < 2 or len(request.form['last_name']) < 2:
		valid = False
		flash("Names must be at least two characters long", 'ERROR')
	#validate email
	if len(request.form['email']) < 1:
		valid = False
		flash("Invalid Email", 'ERROR')
	else: #ensure email is not already taken 
		query = "SELECT * FROM users WHERE email=:email"
		user_list = mysql.query_db(query, request.form)
		if len(user_list) > 0:
			valid = False
			flash("Email already in use", 'ERROR')
	#validate password
	if len(request.form["password"]) < 8:
		valid = False
		flash("Password must be at least 8 characters", 'ERROR')
	elif request.form["password"] != request.form["password"]:
		valid = False
		flash("Password must match Confirm Password.", 'ERROR')
	#if all validation is successful, use this SQL query to create a new user record in users table.
	if valid:
		flash("You have successfully registered for The Wall!")
		query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) Values(:first_name, :last_name, :email, :password, NOW(), NOW());"
	#dictionary of my registration form data with password encryption.
		data = {
			"first_name": request.form["first_name"],
			"last_name": request.form["last_name"],
			"email": request.form["email"],
			"password": bcrypt.hashpw(request.form["password"].encode(), bcrypt.gensalt())
		}
	#the query being sent to my database (the_wall). Then redirect users to their "The Wall" page.
		user_id = mysql.query_db(query, data)
		session["name"] = request.form["first_name"]
		session["id"] = user_id
		return redirect("/theWall")
	else: #if validation is not successful, redirect them to the same page to begin again. 
		return redirect("/")

@app.route("/login", methods=["POST"])
def login():
	
	valid = True
	#validate email.
	if len(request.form["email"]) < 1:
		valid = False
		flash("Email is required to login.", 'ERROR2')
	elif not email_regex.match(request.form["email"]):
		valid = False
		flash("Invalid Email", "ERROR2")
	else: #check to see if email exists in users table.
		query = "SELECT * FROM users WHERE email=:email"
		user_list = mysql.query_db(query, request.form)
		if len(user_list) < 1:
			valid = False
			flash("Unknown email", "ERROR2")
	#ensure email meets minimum standards.
	if len(request.form["password"]) < 8:
		valid = False
		flash("Password must be 8 or more characters", "ERROR2")
	#hash password and compare it to pw in users table. 
	if valid:
		if bcrypt.checkpw(request.form["password"].encode(), user_list[0]["password"].encode()):
			flash("You have successfully logged in to The Wall!", "SUCCESS")
			session["name"] = user_list[0]["first_name"]
			session["id"] = user_list[0]["id"]
			return redirect("/theWall")
		else:
			flash("Incorrect password", "ERROR")

	return redirect('/')

@app.route('/theWall')
def theWall():
	if "id" not in session:
		flash("You have to log in first!", "ERROR")
		return redirect("/")
	wallMessages = mysql.query_db("SELECT message, DATE_FORMAT(messages.created_at,'%b %D %l:%i %p') AS created_at, users.first_name, users.last_name, messages.id, messages.user_id FROM users JOIN messages ON messages.user_id = users.id ORDER BY created_at desc;")
	mComments = mysql.query_db("SELECT comment, users.first_name, users.last_name, message_id, DATE_FORMAT(comments.created_at,'%b %D %l:%i %p') AS created_at, comments.user_id, comments.id FROM users JOIN comments ON comments.user_id = users.id;")

	return render_template('thewall.html', wallMessages=wallMessages, mComments=mComments)

@app.route('/logout')
def logout():
	session.clear()
	flash("You have successfully logged out of The Wall.", "SUCCESS")	
	return redirect("/")

@app.route('/message', methods=['POST'])
def message():
	query = "INSERT INTO messages (message, created_at, updated_at, user_id) Values(:message, NOW(), NOW(), :user_id);"
	data = {
		"message": request.form["message"],
		"user_id": session['id']
	}
	mysql.query_db(query, data)

	return redirect("/theWall")

@app.route('/comment', methods=['POST'])
def comment():
	query = "INSERT INTO comments (comment, created_at, updated_at, message_id, user_id) Values(:comment, NOW(), NOW(), :message_id, :user_id);"
	data = {
		"comment": request.form['comment'],
		"message_id": request.form["message_id"],
		"user_id": session['id']
	}
	mysql.query_db(query, data)
	return redirect('/theWall')

@app.route('/delete', methods=['POST'])
def delete():
	query2 = "DELETE FROM comments WHERE message_id = :messageId;"
	data2 = {
		"messageId": request.form['message.id']
	}
	mysql.query_db(query2, data2)

	query = "DELETE FROM messages WHERE id = :messageId;"
	data = {
		"messageId": request.form['message.id']
	}
	mysql.query_db(query, data)	

	return redirect('/theWall')

@app.route('/delete/comment', methods=['POST'])
def deleteComment():
	print request.form['id']
	query = "DELETE FROM comments WHERE id = :commentId;"
	data = {
		"commentId": request.form['id']
	}
	mysql.query_db(query, data)

	return redirect('/theWall')

app.run(debug=True)
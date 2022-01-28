from flask import Flask, render_template, request, redirect, session, url_for
from bson import ObjectId
from pymongo import MongoClient
import os
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

#mysql

app.config['MYSQL_HOST'] = os.environ['MYSQL_HOST']
app.config['MYSQL_USER'] = os.environ['MYSQL_USER']
app.config['MYSQL_PASSWORD'] = os.environ['MYSQL_PASSWORD']
app.config['MYSQL_DB'] = 'databasejay'

mysql = MySQL(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        if result > 0:
            data = cur.fetchone()
            if data:
                session['logged_in'] = True
                session['email'] = email
                return redirect(url_for('all_tutorials'))
            else:
                return "Password incorrect"
        else:
            return "User not found"
    return render_template('login.html')

# mongodb
client = MongoClient(os.environ['MONGODB_URI'])
db = client.get_default_database()
tutorials = db.tutorials

@app.route('/')
# @app.route('/all-tutorials')
def all_tutorials():
  if 'logged_in' in session and 'email' in session:
    logged_in = session['logged_in']
    email = session['email']
    return render_template('all-tutorials.html', tutorials=tutorials.find(), logged_in=logged_in, email=email)
  else:
    return render_template('all-tutorials.html', tutorials=tutorials.find(), logged_in=False, email=None)

@app.route('/add-tutorial', methods=['GET', 'POST'])
def add_tutorial():
  if request.method == 'POST':
    tutorial = {
      'title': request.form['title'],
      'description': request.form['description'],
      'url': request.form['url']
    }
    tutorials.insert_one(tutorial)
    return redirect(url_for('all_tutorials'))
  return render_template('add-tutorial.html')

@app.route('/edit-tutorial/<tutorial_id>', methods=['GET', 'POST'])
def edit_tutorial(tutorial_id):
  if request.method == 'POST':
    tutorial = {
      'title': request.form['title'],
      'description': request.form['description'],
      'url': request.form['url']
    }
    tutorials.update_one(
      {'_id': ObjectId(tutorial_id)},
      {'$set': tutorial}
    )
    return redirect(url_for('all_tutorials'))
  else:
    tutorial = tutorials.find_one({'_id': ObjectId(tutorial_id)})
    return render_template('edit-tutorial.html', tutorial=tutorial)

@app.route('/delete-tutorial/<tutorial_id>')
def delete_tutorial(tutorial_id):
  tutorials.delete_one({'_id': ObjectId(tutorial_id)})
  return redirect(url_for('all_tutorials'))

@app.route('/tutorial/<tutorial_id>')
def tutorial(tutorial_id):
  return render_template('tutorial.html', tutorial=tutorials.find_one({'_id': ObjectId(tutorial_id)}))

@app.route('/search')
def search():
  query = request.args.get('search')
  return render_template('search.html', query=query, tutorials=tutorials.find({'title': { '$regex': query, '$options': "i" } }))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
  app.secret_key = os.environ['SECRET_KEY']
  app.run(debug=True)
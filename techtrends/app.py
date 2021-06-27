from datetime import time
import logging
from os import name
import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    get_db_connection.counter += 1
    return connection

get_db_connection.counter=0

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

def getPostsCount():
    app.logger.info('getPostsCount')
    connection = get_db_connection()
    count = connection.execute('SELECT COUNT(1) FROM posts').fetchone()
    connection.close()
    return count[0]

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    
    post = get_post(post_id)
    if post is None:
      app.logger.info('A non-existing article is accessed and a 404 page is returned.')
      return render_template('404.html'), 404
    else:
      title = post['title']
      msg = 'Article "{title}" retrieved!'.format(title=title)
      app.logger.info(msg)
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The "About Us" page is retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            msg = '"{title}" was created!'.format(title=title)
            app.logger.info(msg)
            return redirect(url_for('index'))

    return render_template('create.html')

# healthz resource
@app.route('/healthz', methods=['GET'])
def healthz():
    app.logger.info('healthz')
    data = {
        "result": "OK - healthy"
    }
    return jsonify(data), 200, {'Content-Type': 'application/json'}

# metrics resource
@app.route('/metrics', methods=['GET'])
def metrics():
    app.logger.info('metrics')
    totalConns = get_db_connection.counter
    totalPosts = getPostsCount()
    data = {
        "db_connection_count": totalConns,
        "post_count": totalPosts
    }
    return jsonify(data), 200, {'Content-Type': 'application/json'}

# start the application on port 3111
if __name__ == "__main__":
    FORMAT = '%(levelname)s:%(name)s:%(asctime)s, %(message)s'
    DATEFORMAT = '%d/%m/%Y, %H:%M:%S'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=DATEFORMAT)
    app.run(host='0.0.0.0', port='3111')

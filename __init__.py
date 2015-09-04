import sqlite3, config
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

app = Flask(__name__)
app.config.from_pyfile('config.py')

@app.route("/")
def browse():
    cur = g.db.execute('select title, text, url from entries order by title asc')
    entries = [dict(title=row[0], text=row[1], url=row[2]) for row in cur.fetchall()]
    return render_template('browse.html', entries=entries)


@app.route('/admin')
def admin():
    admin_check()

    cur = g.db.execute('select id, title, text, url from entries order by id desc')

    posts = [dict(id=row[0], title=row[1], text=row[2], url=row[3]) for row in cur.fetchall()]

    return render_template('admin.html', posts=posts)


@app.route('/add', methods=['POST'])
def add_entry():
    admin_check()

    g.db.execute('insert into entries (title, text, url) values (?, ?, ?)',
                 [request.form['title'], request.form['text'], request.form['url']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('admin'))


@app.route('/edit_helper', methods=['POST', 'GET'])
def edit_helper():
    admin_check()

    post_id = request.args.get('post')

    title = request.form['title']
    text = request.form['text']
    url = request.form['url']
    g.db.execute("update entries set title=?, text=?, url=? where id=?",
                 (title, text, url, post_id))
    g.db.commit()
    flash('Post was successfully updated')
    return redirect(url_for('admin'))


@app.route('/delete_helper', methods=['GET'])
def delete_helper():
    admin_check()

    post_id = request.args.get('post')

    g.db.execute("delete from entries where id=?", (post_id))
    g.db.commit()
    flash('Post was successfully deleted')
    return redirect(url_for('admin'))

@app.route('/edit_post', methods=['GET'])
def edit_post():
    admin_check()

    post_id = request.args.get('post')

    if post_id:
        # Grab the current information for the selected ID from the database
        post = query_db('select * from entries where id = ?',
                        [post_id], one=True)

        if post is None:
            flash('no such post')
        else:
            return render_template('edit_post.html', post=post)
    else:
        return redirect(url_for('admin'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('admin'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('browse'))


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def admin_check():
    if not session.get('logged_in'):
        abort(404)


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


if __name__ == '__main__':
    app.run()

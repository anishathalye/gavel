# Copyright (c) 2015-2016 Anish Athalye (me@anishathalye.com)
#
# This software is released under AGPLv3. See the included LICENSE.txt for
# details.

import os
import base64
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import func, desc
from datetime import datetime
from numpy.random import (
    choice,
    random,
    shuffle,
)
import crowd_bt
from functools import wraps
import csv
import io
from urlparse import urljoin

from mail import send_judge_email

class SerializableAlchemy(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        if not 'isolation_level' in options:
            # XXX is this slow? are there better ways?
            options['isolation_level'] = 'SERIALIZABLE'
        return super(SerializableAlchemy, self).apply_driver_hacks(app, info, options)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', None) or 'postgresql://localhost/gavel'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gavel-secret')
ADMIN_PASSWORD = os.environ['ADMIN_PASSWORD']
db = SerializableAlchemy(app)

ANNOTATOR_ID = 'annotator_id'

########################################
# Models
########################################

ignore_table = db.Table('ignore',
    db.Column('annotator_id', db.Integer, db.ForeignKey('annotator.id')),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'))
)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    location = db.Column(db.Text)
    description = db.Column(db.Text)

    mu = db.Column(db.Float)
    sigma_sq = db.Column(db.Float)

    def __init__(self, name, location, description):
        self.name = name
        self.location = location
        self.description = description
        self.mu = crowd_bt.MU_PRIOR
        self.sigma_sq = crowd_bt.SIGMA_SQ_PRIOR

class Annotator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    description = db.Column(db.Text)
    secret = db.Column(db.String(32), unique=True, nullable=False)
    next_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    next = db.relationship('Item', foreign_keys=[next_id], uselist=False)
    prev_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    prev = db.relationship('Item', foreign_keys=[prev_id], uselist=False)
    ignore = db.relationship('Item', secondary=ignore_table)

    alpha = db.Column(db.Float)
    beta = db.Column(db.Float)

    def __init__(self, name, email, description):
        self.name = name
        self.email = email
        self.description = description
        self.alpha = crowd_bt.ALPHA_PRIOR
        self.beta = crowd_bt.BETA_PRIOR
        self.secret = gen_secret(32)

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    annotator_id = db.Column(db.Integer, db.ForeignKey('annotator.id'))
    annotator = db.relationship('Annotator', foreign_keys=[annotator_id], uselist=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    winner = db.relationship('Item', foreign_keys=[winner_id], uselist=False)
    loser_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    loser = db.relationship('Item', foreign_keys=[loser_id], uselist=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, annotator, winner, loser):
        self.annotator = annotator
        self.winner = winner
        self.loser = loser

########################################
# Helpers
########################################

def check_auth(username, password):
    return username == 'admin' and password == ADMIN_PASSWORD

def authenticate():
    return Response('Access denied.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def gen_secret(length):
    return base64.b32encode(os.urandom(length))[:length].lower()

def get_annotator_by_secret(secret):
    try:
        annotator = Annotator.query.filter(Annotator.secret == secret).one()
    except NoResultFound:
        annotator = None
    return annotator

def get_annotator_by_id(id):
    if id is None:
        return None
    try:
        annotator = Annotator.query.with_for_update().get(id)
    except NoResultFound:
        annotator = None
    return annotator

def get_item_by_id(id):
    if id is None:
        return None
    try:
        item = Item.query.get(id)
    except NoResultFound:
        item = None
    return item

def maybe_init_annotator(annotator):
    if annotator.next is None:
        # XXX this is inefficient, better to do exclude in a query
        ignored_ids = map(lambda i: i.id, annotator.ignore)
        items = filter(lambda i: i.id not in ignored_ids, Item.query.all())
        if items:
            annotator.next = choice(items)
            db.session.commit()

def get_current_annotator():
    return get_annotator_by_id(session.get(ANNOTATOR_ID, None))

def choose_next(annotator):
    ignored_ids = map(lambda i: i.id, annotator.ignore)
    items = filter(lambda i: i.id not in ignored_ids, Item.query.all())
    shuffle(items)
    if items:
        if random() < crowd_bt.EPSILON:
            return items[0]
        else:
            return crowd_bt.argmax(lambda i: crowd_bt.expected_information_gain(
                annotator.alpha,
                annotator.beta,
                annotator.prev.mu,
                annotator.prev.sigma_sq,
                i.mu,
                i.sigma_sq), items)
    else:
        return None

def perform_vote(annotator, next_won):
    if next_won:
        winner = annotator.next
        loser = annotator.prev
    else:
        winner = annotator.prev
        loser = annotator.next
    u_alpha, u_beta, u_winner_mu, u_winner_sigma_sq, u_loser_mu, u_loser_sigma_sq = crowd_bt.update(
        annotator.alpha,
        annotator.beta,
        winner.mu,
        winner.sigma_sq,
        loser.mu,
        loser.sigma_sq)
    annotator.alpha = u_alpha
    annotator.beta = u_beta
    winner.mu = u_winner_mu
    winner.sigma_sq = u_winner_sigma_sq
    loser.mu = u_loser_mu
    loser.sigma_sq = u_loser_sigma_sq

def data_to_csv_string(data):
    output = io.BytesIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue()

def data_from_csv_string(string):
    input = io.BytesIO(string)
    reader = csv.reader(input)
    return list(reader)

########################################
# Routes / Controllers
########################################

@app.route('/')
def index():
    annotator = get_current_annotator()
    if annotator is None:
        return render_template('logged_out.html')
    else:
        maybe_init_annotator(annotator)
        if annotator.next is None:
            return render_template('wait.html')
        elif annotator.prev is None:
            return render_template('begin.html', item=annotator.next)
        else:
            return render_template('vote.html', prev=annotator.prev, next=annotator.next)

@app.route('/vote', methods=['POST'])
def vote():
    annotator = get_current_annotator()
    if annotator is not None:
        if annotator.prev.id == int(request.form['prev_id']) and annotator.next.id == int(request.form['next_id']):
            if request.form['action'] == 'Skip':
                annotator.ignore.append(annotator.next)
            else:
                if request.form['action'] == 'Previous':
                    perform_vote(annotator, next_won=False)
                    decision = Decision(annotator, winner=annotator.prev, loser=annotator.next)
                elif request.form['action'] == 'Current':
                    perform_vote(annotator, next_won=True)
                    decision = Decision(annotator, winner=annotator.next, loser=annotator.prev)
                db.session.add(decision)
                annotator.prev = annotator.next
                annotator.ignore.append(annotator.prev)
            annotator.next = choose_next(annotator)
            db.session.commit()
    return redirect(url_for('index'))

@app.route('/begin', methods=['POST'])
def begin():
    annotator = get_current_annotator()
    if annotator is not None:
        if annotator.next.id == int(request.form['item_id']):
            annotator.ignore.append(annotator.next)
            if request.form['action'] == 'Done':
                annotator.prev = annotator.next
                annotator.next = choose_next(annotator)
            elif request.form['action'] == 'Skip':
                annotator.next = None # will be reset in index
            db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop(ANNOTATOR_ID, None)
    return redirect(url_for('index'))

@app.route('/login/<secret>')
def login(secret):
    annotator = get_annotator_by_secret(secret)
    if annotator is None:
        session.pop(ANNOTATOR_ID, None)
        session.modified = True
    else:
        session[ANNOTATOR_ID] = annotator.id
    return redirect(url_for('index'))

@app.route('/admin')
@requires_auth
def admin():
    annotators = Annotator.query.all()
    items = Item.query.order_by(desc(Item.mu)).all()
    decisions = Decision.query.all()
    counts = {}
    item_counts = {}
    for d in decisions:
        a = d.annotator_id
        w = d.winner_id
        l = d.loser_id
        counts[a] = counts.get(a, 0) + 1
        item_counts[w] = item_counts.get(w, 0) + 1
        item_counts[l] = item_counts.get(l, 0) + 1
    annotators.sort(key=lambda i: -counts.get(i.id, 0))
    return render_template('admin.html', annotators=annotators, counts=counts, item_counts=item_counts, items=items, votes=len(decisions))

@app.route('/admin/item', methods=['POST'])
@requires_auth
def item():
    action = request.form['action']
    if action == 'Submit':
        csv = request.form['data']
        data = data_from_csv_string(csv.encode('utf8'))
        for row in data:
            item = Item(*row)
            db.session.add(item)
        db.session.commit()
    elif action == 'Delete':
        id = request.form['item_id']
        try:
            db.session.execute(ignore_table.delete(ignore_table.c.item_id == id))
            Item.query.filter_by(id=id).delete()
            db.session.commit()
        except IntegrityError as e:
            return render_template('error.html', message=str(e))
    return redirect(url_for('admin'))

@app.route('/admin/annotator', methods=['POST'])
@requires_auth
def annotator():
    action = request.form['action']
    if action == 'Submit':
        csv = request.form['data']
        data = data_from_csv_string(csv.encode('utf8'))
        for row in data:
            annotator = Annotator(*row)
            db.session.add(annotator)
        db.session.commit()
    elif action == 'Delete':
        id = request.form['annotator_id']
        try:
            db.session.execute(ignore_table.delete(ignore_table.c.annotator_id == id))
            Annotator.query.filter_by(id=id).delete()
            db.session.commit()
        except IntegrityError as e:
            return render_template('error.html', message=str(e))
    elif action == 'Email':
        id = request.form['annotator_id']
        try:
            annotator = Annotator.query.filter_by(id=id).one()
        except (MultipleResultsFound, NoResultFound) as e:
            return render_template('error.html', message='Invalid annotator.')
        magic_link = urljoin(request.url_root, '/login/{secret}'.format(secret=annotator.secret))
        send_judge_email(annotator.name, annotator.email, magic_link)

    return redirect(url_for('admin'))

@app.route('/api/items.csv')
@requires_auth
def item_dump():
    items = Item.query.order_by(desc(Item.mu)).all()
    data = [['Mu', 'Sigma Squared', 'Name', 'Location', 'Description']]
    data += [[str(item.mu), str(item.sigma_sq), item.name, item.location, item.description] for item in items]
    return Response(data_to_csv_string(data), mimetype='text/csv')

@app.route('/api/annotators.csv')
@requires_auth
def annotator_dump():
    annotators = Annotator.query.all()
    data = [['Name', 'Email', 'Description', 'Secret']]
    data += [[str(a.name), a.email, a.description, a.secret] for a in annotators]
    return Response(data_to_csv_string(data), mimetype='text/csv')

if __name__ == '__main__':
    if os.environ.get('DEBUG', False):
        app.debug = True
    app.run(debug=True)

import os
import base64
from models import Item, Annotator, db, NoResultFound
from functools import wraps
import csv
import io
import crowd_bt

from numpy.random import choice, random, shuffle
from flask import Response, request, session
from settings import ADMIN_PASSWORD, ANNOTATOR_ID

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



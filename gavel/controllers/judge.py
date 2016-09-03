from gavel import app
from gavel.models import *
from gavel.constants import *
from gavel.settings import MIN_VIEWS
import gavel.crowd_bt as crowd_bt
from flask import (
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from numpy.random import choice, random, shuffle
from functools import wraps

def requires_open(redirect_to):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if Setting.value_of(SETTING_CLOSED) == SETTING_TRUE:
                return redirect(url_for(redirect_to))
            else:
                return f(*args, **kwargs)
        return decorated
    return decorator

def requires_active_annotator(redirect_to):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            annotator = get_current_annotator()
            if annotator is None or not annotator.active:
                return redirect(url_for(redirect_to))
            else:
                return f(*args, **kwargs)
        return decorated
    return decorator


@app.route('/')
def index():
    annotator = get_current_annotator()
    if annotator is None:
        return render_template('logged_out.html')
    else:
        if Setting.value_of(SETTING_CLOSED) == SETTING_TRUE:
            return render_template('closed.html')
        if not annotator.active:
            return render_template('disabled.html')
        maybe_init_annotator(annotator)
        if annotator.next is None:
            return render_template('wait.html')
        elif annotator.prev is None:
            return render_template('begin.html', item=annotator.next)
        else:
            return render_template('vote.html', prev=annotator.prev, next=annotator.next)

@app.route('/vote', methods=['POST'])
@requires_open(redirect_to='index')
@requires_active_annotator(redirect_to='index')
def vote():
    annotator = get_current_annotator()
    if annotator.prev.id == int(request.form['prev_id']) and annotator.next.id == int(request.form['next_id']):
        if request.form['action'] == 'Skip':
            annotator.ignore.append(annotator.next)
        else:
            # ignore things that were deactivated in the middle of judging
            if annotator.prev.active and annotator.next.active:
                if request.form['action'] == 'Previous':
                    perform_vote(annotator, next_won=False)
                    decision = Decision(annotator, winner=annotator.prev, loser=annotator.next)
                elif request.form['action'] == 'Current':
                    perform_vote(annotator, next_won=True)
                    decision = Decision(annotator, winner=annotator.next, loser=annotator.prev)
                db.session.add(decision)
            annotator.next.viewed.append(annotator) # counted as viewed even if deactivated
            annotator.prev = annotator.next
            annotator.ignore.append(annotator.prev)
        annotator.next = choose_next(annotator)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/begin', methods=['POST'])
@requires_open(redirect_to='index')
@requires_active_annotator(redirect_to='index')
def begin():
    annotator = get_current_annotator()
    if annotator.next.id == int(request.form['item_id']):
        annotator.ignore.append(annotator.next)
        if request.form['action'] == 'Done':
            annotator.next.viewed.append(annotator)
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
    annotator = Annotator.by_secret(secret)
    if annotator is None:
        session.pop(ANNOTATOR_ID, None)
        session.modified = True
    else:
        session[ANNOTATOR_ID] = annotator.id
    return redirect(url_for('index'))

def get_current_annotator():
    return Annotator.by_id(session.get(ANNOTATOR_ID, None))

def preferred_items(annotator):
    '''
    Return a list of preferred items for the given annotator to look at next.

    This method takes into account MIN_VIEWS, and if there are any projects
    that haven't been seen enough times, it returns a list of only those
    projects. Otherwise, it returns all the projects that the annotator hasn't
    seen or skipped.
    '''
    # XXX this is inefficient, better to do exclude in a query
    ignored_ids = {i.id for i in annotator.ignore}
    available_items = [
        i for i in Item.query.all() if i.active and i.id not in ignored_ids
    ]
    less_seen = [i for i in available_items if len(i.viewed) < MIN_VIEWS]

    if less_seen:
        return less_seen
    else:
        return available_items

def maybe_init_annotator(annotator):
    if annotator.next is None:
        items = preferred_items(annotator)
        if items:
            annotator.next = choice(items)
            db.session.commit()

def choose_next(annotator):
    items = preferred_items(annotator)

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
        loser.sigma_sq
    )
    annotator.alpha = u_alpha
    annotator.beta = u_beta
    winner.mu = u_winner_mu
    winner.sigma_sq = u_winner_sigma_sq
    loser.mu = u_loser_mu
    loser.sigma_sq = u_loser_sigma_sq

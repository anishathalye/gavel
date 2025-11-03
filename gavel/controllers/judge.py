from gavel import app
from gavel.models import *
from gavel.constants import *
import gavel.settings as settings
import gavel.utils as utils
import gavel.crowd_bt as crowd_bt
from gavel.firebase_session_auth import hackpsu_auth_required
from flask import (
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from numpy.random import choice, random, shuffle
from functools import wraps
from datetime import datetime

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


@app.route('/health')
def health():
    """Health check endpoint - no auth required"""
    return {'status': 'ok', 'service': 'gavel'}, 200

@app.route('/')
@hackpsu_auth_required
def index():
    annotator = get_current_annotator()

    # db.session.expire_all()

    if Setting.value_of(SETTING_CLOSED) == SETTING_TRUE:
        return render_template(
            'closed.html',
            content=utils.render_markdown(settings.CLOSED_MESSAGE)
        )
    if not annotator.active:
        return render_template(
            'disabled.html',
            content=utils.render_markdown(settings.DISABLED_MESSAGE)
        )
    if not annotator.read_welcome:
        return redirect(url_for('welcome'))
    maybe_init_annotator()
    if annotator.next is None:
        return render_template(
            'wait.html',
            content=utils.render_markdown(settings.WAIT_MESSAGE)
        )
    elif annotator.prev is None:
        return render_template('begin.html', item=annotator.next)
    else:
        return render_template('vote.html', prev=annotator.prev, next=annotator.next)

@app.route('/vote', methods=['POST'])
@requires_open(redirect_to='index')
@hackpsu_auth_required
def vote():
    def tx():
        annotator = get_current_annotator()
        if annotator.prev.id == int(request.form['prev_id']) and annotator.next.id == int(request.form['next_id']):
            notes = request.form.get('notes', '').strip() or None
            if request.form['action'] == 'Skip':
                annotator.ignore.append(annotator.next)
            else:
                # ignore things that were deactivated in the middle of judging
                if annotator.prev.active and annotator.next.active:
                    if request.form['action'] == 'Previous':
                        perform_vote(annotator, next_won=False)
                        decision = Decision(annotator, winner=annotator.prev, loser=annotator.next, notes=notes)
                    elif request.form['action'] == 'Current':
                        perform_vote(annotator, next_won=True)
                        decision = Decision(annotator, winner=annotator.next, loser=annotator.prev, notes=notes)
                    db.session.add(decision)
                annotator.next.viewed.append(annotator) # counted as viewed even if deactivated
                annotator.prev = annotator.next
                annotator.ignore.append(annotator.prev)
            annotator.update_next(choose_next(annotator))
            db.session.commit()
    with_retries(tx)
    return redirect(url_for('index'))

@app.route('/begin', methods=['POST'])
@requires_open(redirect_to='index')
@hackpsu_auth_required
def begin():
    def tx():
        annotator = get_current_annotator()
        if annotator.next.id == int(request.form['item_id']):
            annotator.ignore.append(annotator.next)
            if request.form['action'] == 'Continue':
                annotator.next.viewed.append(annotator)
                annotator.prev = annotator.next
                annotator.update_next(choose_next(annotator))
            elif request.form['action'] == 'Skip':
                annotator.next = None # will be reset in index
            db.session.commit()
    with_retries(tx)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    import os
    session.pop(ANNOTATOR_ID, None)
    # Redirect to HackPSU auth server logout
    auth_logout_url = os.environ.get('AUTH_LOGOUT_URL', 'http://localhost:3000/api/sessionLogout')
    gavel_url = os.environ.get('GAVEL_URL', 'http://localhost:5000')
    return redirect(f'{auth_logout_url}?redirect={gavel_url}')

# Old secret-based login removed - using HackPSU Firebase auth instead
# @app.route('/login/<secret>/')
# def login(secret):
#     annotator = Annotator.by_secret(secret)
#     if annotator is None:
#         session.pop(ANNOTATOR_ID, None)
#         session.modified = True
#     else:
#         session[ANNOTATOR_ID] = annotator.id
#     return redirect(url_for('index'))

@app.route('/welcome/')
@requires_open(redirect_to='index')
@hackpsu_auth_required
def welcome():
    return render_template(
        'welcome.html',
        content=utils.render_markdown(settings.WELCOME_MESSAGE)
    )

@app.route('/welcome/done', methods=['POST'])
@requires_open(redirect_to='index')
@hackpsu_auth_required
def welcome_done():
    def tx():
        annotator = get_current_annotator()
        if request.form['action'] == 'Continue':
            annotator.read_welcome = True
        db.session.commit()
    with_retries(tx)
    return redirect(url_for('index'))

def get_current_annotator():
    return Annotator.by_id(session.get(ANNOTATOR_ID, None))

def preferred_items(annotator):
    '''
    Return a list of preferred items for the given annotator to look at next.

    This method uses a variety of strategies to try to select good candidate
    projects.
    '''
    items = []
    ignored_ids = {i.id for i in annotator.ignore}

    if ignored_ids:
        available_items = Item.query.filter(
            (Item.active == True) & (~Item.id.in_(ignored_ids))
        ).all()
    else:
        available_items = Item.query.filter(Item.active == True).all()

    prioritized_items = [i for i in available_items if i.prioritized]

    items = prioritized_items if prioritized_items else available_items

    annotators = Annotator.query.filter(
        (Annotator.active == True) & (Annotator.next != None) & (Annotator.updated != None)
    ).all()
    busy = {i.next.id for i in annotators if \
        (datetime.utcnow() - i.updated).total_seconds() < settings.TIMEOUT * 60}
    nonbusy = [i for i in items if i.id not in busy]
    preferred = nonbusy if nonbusy else items

    less_seen = [i for i in preferred if len(i.viewed) < settings.MIN_VIEWS]

    return less_seen if less_seen else preferred

def maybe_init_annotator():
    def tx():
        annotator = get_current_annotator()
        if annotator.next is None:
            items = preferred_items(annotator)
            if items:
                annotator.update_next(choice(items))
                db.session.commit()
    with_retries(tx)

def choose_next(annotator):
    items = preferred_items(annotator)

    shuffle(items) # useful for argmax case as well in the case of ties
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

from flask import jsonify

@app.route('/api/judge_notes')
@hackpsu_auth_required
def get_judge_notes():
    annotator = get_current_annotator()

    # Retrieve all notes made by this judge (if stored in Decision model)
    decisions = Decision.query.filter_by(annotator_id=annotator.id).all()

    # Build a clean list of notes and associated project names
    notes = []
    for d in decisions:
        if d.notes:  # only include those with actual notes
            notes.append({
                "project": d.winner.name if d.winner else "(Unknown Project)",
                "note": d.notes
                
            })
            

    # Sort newest first 
    notes = sorted(notes, key=lambda x: x["project"].lower())

    return jsonify(notes)


@app.route('/api/all_notes')
@hackpsu_auth_required
def all_notes():
    """Return all projects (winner or loser) and all notes from all judges."""
    decisions = Decision.query.filter(Decision.notes.isnot(None)).all()

    data = {}

    for d in decisions:
        # For each decision, include the winner and loser projects if they exist
        projects = []
        if d.winner:
            projects.append(d.winner.name)
        if d.loser:
            projects.append(d.loser.name)

        for project_name in projects:
            if project_name not in data:
                data[project_name] = []
            note_text = d.notes.strip()
            if note_text and note_text not in data[project_name]:
                data[project_name].append(note_text)

    # Convert dict → list for frontend
    formatted = [{"project": name, "notes": notes} for name, notes in data.items()]
    formatted.sort(key=lambda x: x["project"].lower())

    return jsonify(formatted)


#automatic redirect when judging closes
@app.route('/api/status')
def status():
    """Returns whether judging is closed."""
    # db.session.expire_all()  #  Make sure we check fresh DB data
    is_closed = Setting.value_of(SETTING_CLOSED) == SETTING_TRUE
    return jsonify({"closed": is_closed})


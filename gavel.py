# Copyright (c) 2015-2016 Anish Athalye (me@anishathalye.com)
#
# This software is released under AGPLv3. See the included LICENSE.txt for
# details.

import os
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from models import (
    Annotator,
    Decision,
    IntegrityError,
    Item,
    db,
    desc,
    ignore_table,
)
import utils
from settings import DB_URI, SECRET_KEY, PORT
from constants import ANNOTATOR_ID


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY
db.app = app
db.init_app(app)

@app.route('/')
def index():
    annotator = utils.get_current_annotator()
    if annotator is None:
        return render_template('logged_out.html')
    else:
        utils.maybe_init_annotator(annotator)
        if annotator.next is None:
            return render_template('wait.html')
        elif annotator.prev is None:
            return render_template('begin.html', item=annotator.next)
        else:
            return render_template('vote.html', prev=annotator.prev, next=annotator.next)

@app.route('/vote', methods=['POST'])
def vote():
    annotator = utils.get_current_annotator()
    if annotator is not None:
        if annotator.prev.id == int(request.form['prev_id']) and annotator.next.id == int(request.form['next_id']):
            if request.form['action'] == 'Skip':
                annotator.ignore.append(annotator.next)
            else:
                if request.form['action'] == 'Previous':
                    utils.perform_vote(annotator, next_won=False)
                    decision = Decision(annotator, winner=annotator.prev, loser=annotator.next)
                elif request.form['action'] == 'Current':
                    utils.perform_vote(annotator, next_won=True)
                    decision = Decision(annotator, winner=annotator.next, loser=annotator.prev)
                db.session.add(decision)
                annotator.next.viewed.append(annotator)
                annotator.prev = annotator.next
                annotator.ignore.append(annotator.prev)
            annotator.next = utils.choose_next(annotator)
            db.session.commit()
    return redirect(url_for('index'))

@app.route('/begin', methods=['POST'])
def begin():
    annotator = utils.get_current_annotator()
    if annotator is not None:
        if annotator.next.id == int(request.form['item_id']):
            annotator.ignore.append(annotator.next)
            if request.form['action'] == 'Done':
                annotator.next.viewed.append(annotator)
                annotator.prev = annotator.next
                annotator.next = utils.choose_next(annotator)
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

@app.route('/admin')
@utils.requires_auth
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
@utils.requires_auth
def item():
    action = request.form['action']
    if action == 'Submit':
        csv = request.form['data']
        data = utils.data_from_csv_string(csv)
        for row in data:
            _item = Item(*row)
            db.session.add(_item)
        db.session.commit()
    elif action == 'Delete':
        item_id = request.form['item_id']
        try:
            db.session.execute(ignore_table.delete(ignore_table.c.item_id == item_id))
            Item.query.filter_by(id=item_id).delete()
            db.session.commit()
        except IntegrityError as e:
            return render_template('error.html', message=str(e))
    return redirect(url_for('admin'))

@app.route('/admin/annotator', methods=['POST'])
@utils.requires_auth
def annotator_dash():
    action = request.form['action']
    if action == 'Submit':
        csv = request.form['data']
        data = utils.data_from_csv_string(csv)
        for row in data:
            annotator = Annotator(*row)
            db.session.add(annotator)
        db.session.commit()
    elif action == 'Delete':
        annotator_id = request.form['annotator_id']
        try:
            db.session.execute(ignore_table.delete(ignore_table.c.annotator_id == annotator_id))
            Annotator.query.filter_by(id=id).delete()
            db.session.commit()
        except IntegrityError as e:
            return render_template('error.html', message=str(e))
    return redirect(url_for('admin'))

@app.route('/api/items.csv')
@utils.requires_auth
def item_dump():
    items = Item.query.order_by(desc(Item.mu)).all()
    data = [['Mu', 'Sigma Squared', 'Name', 'Location', 'Description']]
    data += [[str(item.mu), str(item.sigma_sq), item.name, item.location, item.description] for item in items]
    return Response(utils.data_to_csv_string(data), mimetype='text/csv')

@app.route('/api/annotators.csv')
@utils.requires_auth
def annotator_dump():
    annotators = Annotator.query.all()
    data = [['Name', 'Email', 'Description', 'Secret']]
    data += [[str(a.name), a.email, a.description, a.secret] for a in annotators]
    return Response(utils.data_to_csv_string(data), mimetype='text/csv')

if __name__ == '__main__':
    if os.environ.get('DEBUG', False):
        app.debug = True
    port = PORT
    app.run(host='0.0.0.0', port=port)

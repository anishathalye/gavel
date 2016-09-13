from gavel import app
from gavel.models import *
from gavel.constants import *
import gavel.settings as settings
import gavel.utils as utils
from flask import (
    redirect,
    render_template,
    request,
    url_for,
)
import urllib.parse

@app.route('/admin/')
@utils.requires_auth
def admin():
    annotators = Annotator.query.order_by(Annotator.id).all()
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
    # settings
    setting_closed = Setting.value_of(SETTING_CLOSED) == SETTING_TRUE
    return render_template(
        'admin.html',
        annotators=annotators,
        counts=counts,
        item_counts=item_counts,
        items=items,
        votes=len(decisions),
        setting_closed=setting_closed,
    )

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
    elif action == 'Prioritize' or action == 'Cancel':
        item_id = request.form['item_id']
        target_state = action == 'Prioritize'
        Item.by_id(item_id).prioritized = target_state
        db.session.commit()
    elif action == 'Disable' or action == 'Enable':
        item_id = request.form['item_id']
        target_state = action == 'Enable'
        Item.by_id(item_id).active = target_state
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
def annotator():
    action = request.form['action']
    if action == 'Submit':
        csv = request.form['data']
        data = utils.data_from_csv_string(csv)
        added = []
        for row in data:
            annotator = Annotator(*row)
            added.append(annotator)
            db.session.add(annotator)
        db.session.commit()
        try:
            email_invite_links(added)
        except Exception as e:
            return render_template('error.html', message=str(e))
    elif action == 'Email':
        annotator_id = request.form['annotator_id']
        try:
            email_invite_links(Annotator.by_id(annotator_id))
        except Exception as e:
            return render_template('error.html', message=str(e))
    elif action == 'Disable' or action == 'Enable':
        annotator_id = request.form['annotator_id']
        target_state = action == 'Enable'
        Annotator.by_id(annotator_id).active = target_state
        db.session.commit()
    elif action == 'Delete':
        annotator_id = request.form['annotator_id']
        try:
            db.session.execute(ignore_table.delete(ignore_table.c.annotator_id == annotator_id))
            Annotator.query.filter_by(id=annotator_id).delete()
            db.session.commit()
        except IntegrityError as e:
            return render_template('error.html', message=str(e))
    return redirect(url_for('admin'))

@app.route('/admin/setting', methods=['POST'])
@utils.requires_auth
def setting():
    key = request.form['key']
    if key == 'closed':
        action = request.form['action']
        new_value = SETTING_TRUE if action == 'Close' else SETTING_FALSE
        Setting.set(SETTING_CLOSED, new_value)
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/item/<item_id>/')
@utils.requires_auth
def item_detail(item_id):
    item = Item.by_id(item_id)
    if not item:
        return render_template('error.html', message='Item not found.')
    else:
        assigned = Annotator.query.filter(Annotator.next == item).all()
        multiple_views = len(item.viewed) > 1
        return render_template(
            'admin_item.html',
            item=item,
            assigned=assigned,
            multiple_views=multiple_views
        )

def email_invite_links(annotators):
    if settings.DISABLE_EMAIL or annotators is None:
        return
    if not isinstance(annotators, list):
        annotators = [annotators]

    emails = []
    for annotator in annotators:
        link = urllib.parse.urljoin(settings.BASE_URL, '/login/%s' % annotator.secret)
        raw_body = settings.EMAIL_BODY.format(name=annotator.name, link=link)
        body = '\n\n'.join(utils.get_paragraphs(raw_body))
        emails.append((annotator.email, settings.EMAIL_SUBJECT, body))

    utils.send_emails(emails)

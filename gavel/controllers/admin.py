from celery.utils.serialization import jsonify

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
    json)

try:
    import urllib
except ImportError:
    import urllib3
import xlrd

ALLOWED_EXTENSIONS = set(['csv', 'xlsx', 'xls'])


@app.route('/admin/')
@utils.requires_auth
def admin():
    annotators = Annotator.query.order_by(Annotator.id).all()
    items = Item.query.order_by(Item.id).all()
    flags = Flag.query.order_by(Flag.id).all()
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
    viewed = {i.id: {a.id for a in i.viewed} for i in items}
    skipped = {}
    for a in annotators:
        for i in a.ignore:
            if a.id not in viewed[i.id]:
                skipped[i.id] = skipped.get(i.id, 0) + 1
    # settings
    setting_closed = Setting.value_of(SETTING_CLOSED) == SETTING_TRUE
    setting_stop_queue = Setting.value_of(SETTING_STOP_QUEUE) == SETTING_TRUE
    return render_template(
        'admin.html',
        annotators=annotators,
        counts=counts,
        item_counts=item_counts,
        item_count=len(items),
        skipped=skipped,
        items=items,
        votes=len(decisions),
        setting_closed=setting_closed,
        setting_stop_queue=setting_stop_queue,
        flags=flags,
        flag_count=len(flags)
    )


@app.route('/beta')
@utils.requires_auth
def admin_beta():
    annotators = Annotator.query.order_by(Annotator.id).all()
    items = Item.query.order_by(Item.id).all()
    flags = Flag.query.order_by(Flag.id).all()
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
    viewed = {i.id: {a.id for a in i.viewed} for i in items}
    skipped = {}
    for a in annotators:
        for i in a.ignore:
            if a.id not in viewed[i.id]:
                skipped[i.id] = skipped.get(i.id, 0) + 1
    # settings
    setting_closed = Setting.value_of(SETTING_CLOSED) == SETTING_TRUE
    return render_template(
        'admin_ti.html',
        annotators=annotators,
        counts=counts,
        item_counts=item_counts,
        item_count=len(items),
        skipped=skipped,
        items=items,
        votes=len(decisions),
        setting_closed=setting_closed,
        flags=flags,
        flag_count=len(flags)
    )


@app.route('/admin/item', methods=['POST'])
@utils.requires_auth
def item():
    action = request.form['action']
    if action == 'Submit':
        data = parse_upload_form()
        if data:
            # validate data
            for index, row in enumerate(data):
                if len(row) != 3:
                    return utils.user_error('Bad data: row %d has %d elements (expecting 3)' % (index + 1, len(row)))
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
            return utils.server_error(str(e))
    return redirect(url_for('admin'))


@app.route('/admin/queueshutdown', methods=['POST'])
@utils.requires_auth
def queue_shutdown():
    action = request.form['action']
    print(action, " *** action")
    annotators = Annotator.query.order_by(Annotator.id).all()
    if action == 'queue':
        for an in annotators:
            an.stop_next = True
        Setting.set(SETTING_STOP_QUEUE, True)
        db.session.commit()
    elif action == 'dequeue':
        for an in annotators:
            an.stop_next = False
        Setting.set(SETTING_STOP_QUEUE, False)
        db.session.commit()

    return redirect(url_for('admin'))


@app.route('/admin/report', methods=['POST'])
@utils.requires_auth
def flag():
    action = request.form['action']
    if action == 'resolve':
        flag_id = request.form['flag_id']
        target_state = action == 'resolve'
        Flag.by_id(flag_id).resolved = target_state
        db.session.commit()
    elif action == 'open':
        flag_id = request.form['flag_id']
        target_state = 1 == 2
        Flag.by_id(flag_id).resolved = target_state
        db.session.commit()
    return redirect(url_for('admin'))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_upload_form():
    f = request.files.get('file')
    data = []
    if f and allowed_file(f.filename):
        extension = str(f.filename.rsplit('.', 1)[1].lower())
        if extension == "xlsx" or extension == "xls":
            workbook = xlrd.open_workbook(file_contents=f.read())
            worksheet = workbook.sheet_by_index(0)
            data = list(utils.cast_row(worksheet.row_values(rx, 0, 3)) for rx in range(worksheet.nrows) if
                        worksheet.row_len(rx) == 3)
        elif extension == "csv":
            data = utils.data_from_csv_string(f.read().decode("utf-8"))
    else:
        csv = request.form['data']
        data = utils.data_from_csv_string(csv)
    return data


@app.route('/admin/item_patch', methods=['POST'])
@utils.requires_auth
def item_patch():
    item = Item.by_id(request.form['item_id'])
    if not item:
        return utils.user_error('Item %s not found ' % request.form['item_id'])
    if 'location' in request.form:
        item.location = request.form['location']
    if 'name' in request.form:
        item.name = request.form['name']
    if 'description' in request.form:
        item.description = request.form['description']
    db.session.commit()
    return redirect(url_for('item_detail', item_id=item.id))


@app.route('/admin/annotator', methods=['POST'])
@utils.requires_auth
def annotator():
    action = request.form['action']
    if action == 'Submit':
        data = parse_upload_form()
        added = []
        if data:
            # validate data
            for index, row in enumerate(data):
                if len(row) != 3:
                    return utils.user_error('Bad data: row %d has %d elements (expecting 3)' % (index + 1, len(row)))
            for row in data:
                annotator = Annotator(*row)
                added.append(annotator)
                db.session.add(annotator)
            db.session.commit()
            try:
                email_invite_links(added)
            except Exception as e:
                return utils.server_error(str(e))
    elif action == 'Email':
        annotator_id = request.form['annotator_id']
        try:
            email_invite_links(Annotator.by_id(annotator_id))
        except Exception as e:
            return utils.server_error(str(e))
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
            return utils.server_error(str(e))
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
        return utils.user_error('Item %s not found ' % item_id)
    else:
        assigned = Annotator.query.filter(Annotator.next == item).all()
        viewed_ids = {i.id for i in item.viewed}
        if viewed_ids:
            skipped = Annotator.query.filter(
                Annotator.ignore.contains(item) & ~Annotator.id.in_(viewed_ids)
            )
        else:
            skipped = Annotator.query.filter(Annotator.ignore.contains(item))
        return render_template(
            'admin_item.html',
            item=item,
            assigned=assigned,
            skipped=skipped
        )


@app.route('/admin/annotator/<annotator_id>/')
@utils.requires_auth
def annotator_detail(annotator_id):
    annotator = Annotator.by_id(annotator_id)
    if not annotator:
        return utils.user_error('Annotator %s not found ' % annotator_id)
    else:
        seen = Item.query.filter(Item.viewed.contains(annotator)).all()
        ignored_ids = {i.id for i in annotator.ignore}
        if ignored_ids:
            skipped = Item.query.filter(
                Item.id.in_(ignored_ids) & ~Item.viewed.contains(annotator)
            )
        else:
            skipped = []
        return render_template(
            'admin_annotator.html',
            annotator=annotator,
            login_link=annotator_link(annotator),
            seen=seen,
            skipped=skipped
        )


@app.route('/admin/live')
@utils.requires_auth
def admin_live():
    annotators = Annotator.query.order_by(Annotator.id).all()
    items = Item.query.order_by(Item.id).all()
    flags = Flag.query.order_by(Flag.id).all()
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
    viewed = {i.id: {a.id for a in i.viewed} for i in items}
    skipped = {}
    for a in annotators:
        for i in a.ignore:
            if a.id not in viewed[i.id]:
                skipped[i.id] = skipped.get(i.id, 0) + 1
    # settings
    setting_closed = Setting.value_of(SETTING_CLOSED) == SETTING_TRUE

    annotators_padded = []
    max_annotator_id = 0
    for an in annotators:
        annotators_padded.insert(int(an.id), an)
        max_annotator_id = an.id if an.id > max_annotator_id else max_annotator_id

    annotators_padded_final = []
    for i in range(max_annotator_id):
        annotators_padded_final.append(None)
    for an in annotators:
        try:
            annotators_padded_final.insert(int(an.id), an)
        except:
            annotators_padded_final.append(None)

    items_padded = []
    max_item_id = 0
    for it in items:
        items_padded.insert(int(it.id), it)
        max_item_id = it.id if it.id > max_item_id else max_item_id

    items_padded_final = []
    for i in range(max_item_id):
        items_padded_final.append(None)
    for it in items:
        try:
            items_padded_final.insert(int(it.id), it)
        except:
            items_padded_final.append(None)

    max_flag_id = 0
    flags_padded = []
    for fl in flags:
        flags_padded.insert(int(fl.id), fl)
        max_flag_id = fl.id if fl.id > max_flag_id else max_flag_id

    flags_padded_final = []
    # TODO: Use index object to track current index in flags_padded
    for i in range(max_flag_id):
        flags_padded_final.append(None)
    for fl in flags:
        try:
            flags_padded_final.insert(int(fl.id), fl)
        except:
            flags_padded_final.append(None)

    ret = {"annotators": [an.to_dict() if an else {'null': 'null'} for an in annotators_padded_final],
           "counts": counts,
           "item_count": len(items),
           "skipped": [sk for sk in skipped],
           "items": [it.to_dict() if it else {'null': 'null'} for it in items_padded_final],
           "votes": len(decisions),
           "setting_closed": setting_closed,
           "flags": [fl.to_dict() if fl else {'null': 'null'} for fl in flags_padded_final],
           "flag_count": len(flags)
           }

    response = app.response_class(
        response=json.dumps(ret),
        status=200,
        mimetype='application/json'
    )
    return response

    # annotators = annotators,
    # counts = counts,
    # item_counts = item_counts,
    # item_count = len(items),
    # skipped = skipped,
    # items = items,
    # votes = len(decisions),
    # setting_closed = setting_closed,
    # flags = flags,
    # flag_count = len(flags)


def annotator_link(annotator):
    return urllib.parse.urljoin(settings.BASE_URL, url_for('login', secret=annotator.secret))


def email_invite_links(annotators):
    if settings.DISABLE_EMAIL or annotators is None:
        return
    if not isinstance(annotators, list):
        annotators = [annotators]

    emails = []
    for annotator in annotators:
        link = annotator_link(annotator)
        raw_body = settings.EMAIL_BODY.format(name=annotator.name, link=link)
        body = '\n\n'.join(utils.get_paragraphs(raw_body))
        emails.append((annotator.email, settings.EMAIL_SUBJECT, body))

    utils.send_emails.delay(emails)

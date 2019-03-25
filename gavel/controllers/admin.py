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
import xlrd

ALLOWED_EXTENSIONS = set(['csv', 'xlsx', 'xls'])

@app.route('/admin/')
@utils.requires_auth
def admin():
    annotators = Annotator.query.order_by(Annotator.id).all()
    items = Item.query.order_by(Item.id).all()
    categories = Category.query.order_by(Category.id).all()
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
    viewed = {}
    for item in items:
        viewed_item = set()
        for item_category in item.categories:
            for annotator in item_category.viewed:
                viewed_item.add(annotator.id)
        viewed[item.id] = viewed_item
    skipped = {}

    for a in annotators:
        for annotator_category in a.categories:
            for i in annotator_category.ignore:
                if a.id not in viewed[i.id]:
                    skipped[i.id] = skipped.get(i.id, 0) + 1

    # settings
    setting_closed = Setting.value_of(SETTING_CLOSED) == SETTING_TRUE
    return render_template(
        'admin.html',
        annotators=annotators,
        counts=counts,
        item_counts=item_counts,
        skipped=skipped,
        items=items,
        viewed=viewed,
        categories=categories,
        votes=len(decisions),
        setting_closed=setting_closed,
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
                if len(row) < 3:
                    return utils.user_error('Bad data: row %d has %d elements (expecting at least 3)' % (index + 1, len(row)))
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
            data = list(utils.cast_row(worksheet.row_values(rx, 0, 3)) for rx in range(worksheet.nrows) if worksheet.row_len(rx) == 3)
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
    action = request.form['action']
    if action == 'Add Category':
        category = Category.by_id(request.form['category_id'])
        if not category:
            return utils.user_error('Category %s not found ' % request.form['category_id'])
        item.categories.append(ItemCategory(item.id, category.id))

    elif action == 'Delete Category':
        item_category_id = request.form['item_category_id']
        ItemCategory.query.filter_by(id=item_category_id).delete()

    elif action == 'Update':
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


@app.route('/admin/annotator_patch', methods=['POST'])
@utils.requires_auth
def annotator_patch():
    annotator = Annotator.by_id(request.form['annotator_id'])
    if not annotator:
        return utils.user_error('Item %s not found ' % request.form['item_id'])
    action = request.form['action']
    if action == 'Add Category':
        category = Category.by_id(request.form['category_id'])
        if not category:
            return utils.user_error('Category %s not found ' % request.form['category_id'])
        annotator.categories.append(AnnotatorCategory(annotator.id, category.id))

    elif action == 'Delete Category':
        annotator_category_id = request.form['annotator_category_id']
        AnnotatorCategory.query.filter_by(id=annotator_category_id).delete()

    db.session.commit()

    return redirect(url_for('annotator_detail', annotator_id=annotator.id))


@app.route('/admin/category_patch', methods=['POST'])
@utils.requires_auth
def category_patch():
    category = Category.by_id(request.form['category_id'])
    if not category:
        return utils.user_error('Item %s not found ' % request.form['category_id'])
    if 'name' in request.form:
        category.name = request.form['name']
    if 'description' in request.form:
        category.description = request.form['description']
    db.session.commit()
    return redirect(url_for('category_detail', category_id=category.id))


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
                if len(row) < 3:
                    return utils.user_error('Bad data: row %d has %d elements (expecting at least 3)' % (index + 1, len(row)))
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


@app.route('/admin/category/<category_id>/')
@utils.requires_auth
def category_detail(category_id):
    category = Category.by_id(category_id)
    if not category:
        return utils.user_error('Category %s not found ' % category_id)
    else:
        decisions = Decision.query.filter(Decision.category_id == category.id).all()
        counts = {}
        item_counts = {}
        for d in decisions:
            a = d.annotator_id
            w = d.winner_id
            l = d.loser_id
            counts[a] = counts.get(a, 0) + 1
            item_counts[w] = item_counts.get(w, 0) + 1
            item_counts[l] = item_counts.get(l, 0) + 1

        viewed = {
            i.item_id: {a.id for a in i.viewed}
            for i in category.items
        }
        skipped = {}
        for annotator_category in category.annotators:
            for i in annotator_category.ignore:
                if annotator_category.annotator_id not in viewed.get(i.id, {}):
                    skipped[i.id] = skipped.get(i.id, 0) + 1
        return render_template(
            'admin_category.html',
            category=category,
            items=category.items,
            annotators=category.annotators,
            item_counts=item_counts,
            viewed=viewed,
            skipped=skipped,
            counts=counts
        )


@app.route('/admin/item/<item_id>/')
@utils.requires_auth
def item_detail(item_id):
    item = Item.by_id(item_id)
    if not item:
        return utils.user_error('Item %s not found ' % item_id)
    else:
        category_ids = [
            category.category_id for category in item.categories
        ]
        categories = Category.query.order_by(Category.id).filter(~Category.id.in_(category_ids))

        acs = AnnotatorCategory.query.filter(AnnotatorCategory.next == item).all()
        assigned = [ac.annotator for ac in acs]
        item_categories = ItemCategory.query.filter(ItemCategory.item == item).all()
        viewed_ids = {}
        for ic in item_categories:
            for viewed in ic.viewed:
                viewed_ids[viewed.id] = True

        if viewed_ids:
            skipped = AnnotatorCategory.query.filter(
                AnnotatorCategory.ignore.contains(item) & ~AnnotatorCategory.annotator_id.in_(viewed_ids)
            )
        else:
            skipped = AnnotatorCategory.query.filter(AnnotatorCategory.ignore.contains(item))

        skipped = [annotator_category.annotator for annotator_category in skipped]
        return render_template(
            'admin_item.html',
            item=item,
            assigned=assigned,
            skipped=skipped,
            categories=categories
        )

@app.route('/admin/annotator/<annotator_id>/')
@utils.requires_auth
def annotator_detail(annotator_id):
    annotator = Annotator.by_id(annotator_id)
    if not annotator:
        return utils.user_error('Annotator %s not found ' % annotator_id)
    else:
        category_ids = [
            category.category_id for category in annotator.categories
        ]
        categories = Category.query.order_by(Category.id).filter(~Category.id.in_(category_ids))

        seen = [
            ic.item_id
            for ic in ItemCategory.query.filter(ItemCategory.viewed.contains(annotator)).all()
        ]

        ignored_ids = set()
        for annotator_category in annotator.categories:
            for i in annotator_category.ignore:
                ignored_ids.add(i.id)

        if ignored_ids:
            skipped = Item.query.join(Item.categories).filter(
                Item.id.in_(ignored_ids) & ~ItemCategory.viewed.contains(annotator)
            )
        else:
            skipped = []
        return render_template(
            'admin_annotator.html',
            annotator=annotator,
            login_link=annotator_link(annotator),
            seen=seen,
            skipped=skipped,
            categories=categories
        )

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


@app.route('/admin/category', methods=['POST'])
@utils.requires_auth
def category():
    action = request.form['action']
    if action == 'Submit':
        data = parse_upload_form()
        if data:
            # validate data
            for index, row in enumerate(data):
                if len(row) != 2:
                    return utils.user_error('Bad data: row %d has %d elements (expecting 3)' % (index + 1, len(row)))
            for row in data:
                _item = Category(*row)
                db.session.add(_item)
            db.session.commit()
    elif action == 'Disable' or action == 'Enable':
        category_id = request.form['category_id']
        target_state = action == 'Enable'
        Category.by_id(category_id).active = target_state
        db.session.commit()
    elif action == 'Delete':
        category_id = request.form['category_id']
        try:
            Category.query.filter_by(id=category_id).delete()
            db.session.commit()
        except IntegrityError as e:
            return utils.server_error(str(e))
    return redirect(url_for('admin'))

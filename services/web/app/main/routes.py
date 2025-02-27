from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, current_app, send_from_directory, jsonify
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from sqlalchemy import func, and_, or_
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from authlib.integrations.flask_client import OAuth
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, MessageForm
from app.models import Model, User, Post, Message, Notification, Vote
from app.translate import translate
from app.main import bp
from werkzeug.utils import secure_filename
import os



@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    # Query to count suggested names
    models = db.session.execute(sa.select(Model)).scalars().all()
    model_list = []
    for model in models:
        model_list.append({
            "name": model.name,
            "image": model.image,
            "description": model.description,
            "instagram": model.instagram,
            "height": model.height,
            "agency": model.agency,
            "specialization": model.specialization,
            "location": model.location,
            "experience": model.experience,
            "highlights": model.highlights,
            "notable_work": model.notable_work,
            "weight": model.weight,
            "measurements": model.measurements,
            "hair_color": model.hair_color,
            "eye_color": model.eye_color,
            "media_links": model.media_links,
        })
    return render_template('index.html', models=model_list)

@bp.route('/models')
def model_list():
    models = db.session.execute(sa.select(Model)).scalars().all()
    return render_template('models.html', models=models)

@bp.route("/models/<name>")
def detail(name):
    model = db.session.execute(sa.select(Model).filter_by(name=name)).scalar()
    if model:
        model.image_url = url_for('static', filename=model.image)
        return render_template("model.html", model=model)
    return "Model not found", 404


@bp.route("/model/<name>")
def details(name):
    model = db.session.execute(sa.select(Model).filter_by(name=name)).scalar()
    if model:
        model.image_url = url_for('static', filename=model.image)
        return render_template("model_details.html", model=model)
    return "Model not found", 404


@bp.route("/api/models")
def api_models():
    models = db.session.execute(sa.select(Model)).scalars().all()
    return jsonify(models)


@bp.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user,
                    language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.home'))
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.home', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.home', page=posts.prev_num) \
        if posts.has_prev else None
    
    return render_template('home.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/explore')
#@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('home.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
#@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items, title=user.username,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.home'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.home'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.home'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.home'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    data = request.get_json()
    return {'text': translate(data['text'],
                              data['source_language'],
                              data['dest_language'])}


'''
@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
   
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)
'''


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.first_or_404(sa.select(User).where(User.username == recipient))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count',
                              user.unread_message_count())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    query2 = current_user.messages_sent.select().order_by(
        Message.timestamp.desc())
    messages = db.paginate(query, page=page,
                           per_page=current_app.config['POSTS_PER_PAGE'],
                           error_out=False)
    messages2 = db.paginate(query2, page=page,
                           per_page=current_app.config['POSTS_PER_PAGE'],
                           error_out=False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    next_url2 = url_for('main.messages', page=messages2.next_num) \
        if messages2.has_next else None
    prev_url2 = url_for('main.messages', page=messages2.prev_num) \
        if messages2.has_prev else None
    
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url, messages2=messages2.items,
                           next_url2=next_url2, prev_url2=prev_url2, title=_('Messages'))


@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalars(query)
    return [{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications]


'''
@bp.route('/<name>', methods=['GET', 'POST'])
def name_search(name):
    
    if request.method == "POST":
        # list of links to stick name into
        name = (request.form['name']).capitalize()
    
    return render_template('name_search.html', name=name, title=_('Name Search'))
'''

@bp.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(current_app.config["STATIC_FOLDER"], filename)


@bp.route("/media/<path:filename>")
def mediafiles(filename):
    return send_from_directory(current_app.config["MEDIA_FOLDER"], filename)


@bp.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and not allowed_file(file.filename):
            flash('Not allowed file type')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Ensure the media folder exists
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            flash('File uploaded!', 'success')
            return redirect(url_for('main.download_file', name=filename))
    return render_template('upload.html', title=_('Upload New File'))

@bp.route('/upload/<name>')
def download_file(name):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], name)


'''
@bp.route('/search', methods=['GET', 'POST'])
#@login_required
def search():
    models = None  # Initialize models to None
    error = None
    if request.method == 'POST':
        if request.form.get('b_name', None):
            b_name = request.form['b_name']
            name = f"%{b_name}%"  # Use f-strings for cleaner formatting
            print(name)
            models = Model.query.filter(Model.name.ilike(name)).order_by(Model.name.asc()).all()
            if not models:
                error = 'No such model name'

        elif request.form.get('b_location', None):
            b_location = request.form['b_location']
            location = f"%{b_location}%"
            models = Model.query.filter(Model.location.ilike(location)).order_by(Model.location.asc()).all()
            if not models:
                error = 'No such model location'

        elif request.form.get('b_height', None):
            try: # Handle potential ValueError if the input is not a valid number
                b_height = float(request.form['b_height'])
                models = Model.query.filter(Model.height == b_height).order_by(Model.height.asc()).all()  # Exact match for height
                if not models:
                    error = 'No models with that height'
            except ValueError:
                error = "Invalid height value. Please enter a number."

        else:  # Display some default models if no search criteria are provided
            error = 'Showing some models'
            models = Model.query.order_by(func.random()).limit(9).all()

    # if it's a GET request or no search criteria given after POST, show some models:
    if not models:
        models = Model.query.order_by(func.random()).limit(9).all() # Display default models when page is initially loaded.

    return render_template("search.html", models=models, error=error)
'''


@bp.route('/search', methods=['GET', 'POST'])
def search():
    models = None
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        specialization = request.form.get('specialization')
        hair_color = request.form.get('hair_color')
        eye_color = request.form.get('eye_color')
        height = request.form.get('height')
        weight = request.form.get('weight')
        agency = request.form.get('agency')

        filters = []
        if name:
            filters.append(Model.name.ilike(f"%{name}%"))
        if location:
            filters.append(Model.location.ilike(f"%{location}%"))
        if specialization:
            filters.append(Model.specialization.ilike(f"%{specialization}%"))
        if hair_color:
            filters.append(Model.hair_color.ilike(f"%{hair_color}%"))
        if eye_color:
            filters.append(Model.eye_color.ilike(f"%{eye_color}%"))
        if height:
            filters.append(Model.height == height)
        if weight:
            filters.append(Model.weight == weight)
        if agency:
            filters.append(Model.agency == agency)

        if filters:
            models = Model.query.filter(and_(*filters)).all()
            print(models)
    
    return render_template('search2.html', models=models)




def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

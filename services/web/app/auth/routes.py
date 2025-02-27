from flask import render_template, redirect, url_for, flash, request, session
from urllib.parse import urlsplit
from flask_login import login_user, logout_user, current_user
from flask_babel import _
import sqlalchemy as sa
import uuid
from app import db, oauth
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Vote
from app.auth.email import send_password_reset_email
from authlib.integrations.base_client.errors import OAuthError


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))

        flash(_('Welcome %(username)s !!!', username=user.username))    
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route('/logout')
def logout():
    logout_user()
    flash(_('You are now logged out!'))
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Welcome %(username)s !!!', username=user.username))
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', title=_('Register'),
                           form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@bp.route('/login/google')
def google_login():
    # Generate a unique nonce and store it in the session
    nonce = str(uuid.uuid4())
    session['nonce'] = nonce
    redirect_uri = url_for('auth.google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)


@bp.route('/login/google/authorize')
def google_authorize():
    try:
        token = oauth.google.authorize_access_token()
    except OAuthError as e:
        # Log the error for debugging
        print(f"OAuth error: {e}")
        # Handle specific cases based on the error message
        if 'access_denied' in str(e):
            flash(_('Access denied by user. Please try again.'))
            return redirect(url_for('auth.login'))
        elif 'invalid_request' in str(e):
            flash(_('Invalid request. Please try again.'))
            return redirect(url_for('auth.login'))
        flash(_('OAuth authorization error. Please try again later.'))
        return redirect(url_for('auth.login'))
        

    # Retrieve the nonce from the session
    nonce = session.pop('nonce', None)  # Remove nonce from session after retrieval
    user_info = oauth.google.parse_id_token(token, nonce)
    email = user_info['email']
    username = user_info['name'],
    google_id = user_info['sub']

    # Ensure username is a plain string, not a tuple
    if isinstance(username, tuple):
        username = username[0]  # Extract the string from the tuple


    user = User.get_or_create(email, username, google_id)
    if user.google_id is None:
        user.google_id = user_info['sub']
        db.session.commit()

    flash(_('Welcome %(username)s !!!', username=user.username))    

    login_user(user)
    
    return redirect(url_for('main.index'))

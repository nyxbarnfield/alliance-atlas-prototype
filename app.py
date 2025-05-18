from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
import os

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = "changeme"  # Replace with secure key in production

# --- SQLite Database Config ---
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'atlas.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize SQLAlchemy ---
from models import db, User, Campaign, Membership
db.init_app(app)

# --- ROUTES ---

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip().lower()

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    memberships = Membership.query.filter_by(user_id=user.id).all()

    return render_template('dashboard.html', user=user, memberships=memberships)

@app.route('/campaign/<int:campaign_id>')
def campaign_view(campaign_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    campaign = Campaign.query.get_or_404(campaign_id)
    membership = Membership.query.filter_by(user_id=user.id, campaign_id=campaign.id).first()

    if not membership:
        return "Access denied", 403

    if membership.role == "DM":
        return render_template('dm_campaign_view.html', campaign_name=campaign.name)
    else:
        return render_template('player_campaign_view.html', campaign_name=campaign.name)

# --- Run App ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

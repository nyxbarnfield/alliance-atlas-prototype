from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
import os

# --- Flask Setup ---
app = Flask(__name__)
app.secret_key = "changeme"

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'atlas.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Models ---
from models import db, User, Campaign, Membership
db.init_app(app)

# --- Modular Option Lists ---
from options.race_options import race_list
from options.alignment_options import alignment_list
from options.occupation_options import occupation_list
from options.faction_type_options import faction_type_list
from options.age_range_options import age_range_list

# --- Routes ---

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

@app.route('/campaign/new', methods=['GET', 'POST'])
def create_campaign():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        summary = request.form['summary']
        visibility = request.form['visibility']

        campaign = Campaign(name=name)
        db.session.add(campaign)
        db.session.commit()

        membership = Membership(
            user_id=session['user_id'],
            campaign_id=campaign.id,
            role="DM"
        )
        db.session.add(membership)
        db.session.commit()

        return redirect(url_for('create_faction', campaign_id=campaign.id))

    return render_template('create_campaign.html')

@app.route('/campaign/<int:campaign_id>/faction/new', methods=['GET', 'POST'])
def create_faction(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    if request.method == 'POST':
        # Placeholder save logic
        return redirect(url_for('create_npc', campaign_id=campaign.id))

    return render_template(
        'create_faction.html',
        campaign=campaign,
        alignment_list=alignment_list,
        faction_type_list=faction_type_list
    )

@app.route('/campaign/<int:campaign_id>/npc/new', methods=['GET', 'POST'])
def create_npc(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    factions = []  # Replace with faction query when model is ready

    if request.method == 'POST':
        # Placeholder save logic
        return redirect(url_for('campaign_view', campaign_id=campaign.id))

    return render_template(
    'create_npc.html',
    campaign=campaign,
    factions=factions,
    race_list=race_list,
    alignment_list=alignment_list,
    occupation_list=occupation_list,
    age_range_list=age_range_list
)


# --- Run App ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

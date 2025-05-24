from flask import Flask, flash, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from forms import FactionForm
import os

# --- App & DB Setup ---
app = Flask(__name__)
app.secret_key = "changeme"

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'atlas.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Models ---
from models import (
    db, User, Campaign, Membership,
    Faction, NPC, PlayerCharacter, Relationship,
    MasterFaction, MasterNPC
)
db.init_app(app)

# --- Modular Options ---
from options.alignment_options import alignment_list
from options.occupation_options import occupation_list
from options.faction_type_options import faction_type_list
from options.age_range_options import age_range_list
from options.source_options import source_list
from options.relationship_options import relationship_status_list, disposition_list
from options.species_options import species_list  # Formerly race_list

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
        campaign = Campaign(name=name, summary=summary, visibility=visibility)
        db.session.add(campaign)
        db.session.commit()
        membership = Membership(user_id=session['user_id'], campaign_id=campaign.id, role="DM")
        db.session.add(membership)
        db.session.commit()
        return redirect(url_for('create_faction', campaign_id=campaign.id))
    return render_template('create_campaign.html')

@app.route('/campaign/<int:campaign_id>/faction/new', methods=['GET', 'POST'])
def create_faction(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    used_names = [f.name for f in campaign.factions]
    master_factions = MasterFaction.query.all()

    # --- Check if form submitted ---
    if request.method == 'POST':
        name = request.form.get('name').strip()
        summary = request.form.get('summary')
        faction_type = request.form.get('faction_type')
        base_location = request.form.get('base_location')
        alignment = request.form.get('alignment')
        leader_name = request.form.get('leader_name')
        source = request.form.get('source')

        existing = Faction.query.filter_by(name=name, campaign_id=campaign.id).first()
        if existing:
            error = "A faction with that name already exists in this campaign."
            return render_template(
                'create_faction.html',
                campaign=campaign,
                master_factions=master_factions,
                faction_type_list=faction_type_list,
                alignment_list=alignment_list,
                source_list=source_list,
                used_names=used_names,
                error=error,
                previous_data=request.form
            )

        faction = Faction(
            name=name,
            summary=summary,
            faction_type=faction_type,
            base_location=base_location,
            alignment=alignment,
            leader_name=leader_name,
            source=source,
            campaign_id=campaign.id
        )
        db.session.add(faction)
        db.session.commit()

        return redirect(url_for('create_faction', campaign_id=campaign.id, success=1))

    success = request.args.get("success") == "1"
    return render_template(
        'create_faction.html',
        campaign=campaign,
        master_factions=master_factions,
        faction_type_list=faction_type_list,
        alignment_list=alignment_list,
        source_list=source_list,
        used_names=used_names,
        success=success
    )

@app.route('/campaign/<int:campaign_id>/npc/new', methods=['GET', 'POST'])
def create_npc(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    master_npcs = MasterNPC.query.all()
    if request.method == 'POST':
        name = request.form.get('name').strip()
        species = request.form.get('species')
        occupation = request.form.get('occupation') or request.form.get('occupation_custom')
        age_range = request.form.get('age_range')
        description = request.form.get('description')
        source = request.form.get('source')
        faction_id = request.form.get('faction_id')
        existing = NPC.query.filter_by(name=name, campaign_id=campaign.id).first()
        if existing:
            return "An NPC with that name already exists in this campaign.", 400
        npc = NPC(
            name=name, species=species, occupation=occupation,
            age_range=age_range, description=description,
            source=source, faction_id=faction_id or None,
            campaign_id=campaign.id
        )
        db.session.add(npc)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template(
        'create_npc.html',
        campaign=campaign,
        master_npcs=master_npcs,
        species_list=species_list,
        occupation_list=occupation_list,
        age_range_list=age_range_list
    )

@app.route('/campaign/<int:campaign_id>/claim', methods=['GET', 'POST'])
def claim_pc(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    if request.method == 'POST':
        pc_id = request.form.get("pc_id")
        pc = PlayerCharacter.query.get_or_404(pc_id)
        if pc.is_claimed:
            return "Already claimed", 400
        pc.user_id = user_id
        pc.is_claimed = True
        db.session.commit()
        return redirect(url_for('dashboard'))
    unclaimed_pcs = PlayerCharacter.query.filter_by(campaign_id=campaign.id, is_claimed=False).all()
    return render_template('claim_pc.html', campaign=campaign, unclaimed_pcs=unclaimed_pcs)

@app.route('/campaign/<int:campaign_id>/pc/new', methods=['POST'])
def create_pc(campaign_id):
    name = request.form.get("name")
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    pc = PlayerCharacter(name=name, user_id=user_id, campaign_id=campaign_id, is_claimed=True)
    db.session.add(pc)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/campaign/<int:campaign_id>/relationship/new', methods=['GET', 'POST'])
def create_relationship(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    npcs = NPC.query.filter_by(campaign_id=campaign.id).all()
    pcs = PlayerCharacter.query.filter_by(campaign_id=campaign.id).all()
    if request.method == 'POST':
        source_raw = request.form.get('source_id')
        target_raw = request.form.get('target_id')
        disposition = request.form.get('disposition')
        relationship_status = request.form.get('relationship_status')
        description = request.form.get('description')
        source_type, source_id = source_raw.split('-')
        target_type, target_id = target_raw.split('-')
        rel = Relationship(
            source_id=int(source_id), source_type=source_type,
            target_id=int(target_id), target_type=target_type,
            disposition=disposition, relationship_status=relationship_status,
            description=description, campaign_id=campaign.id
        )
        db.session.add(rel)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template(
        'create_relationship.html',
        npcs=npcs,
        pcs=pcs,
        disposition_list=disposition_list,
        relationship_status_list=relationship_status_list
    )

# --- Run App ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

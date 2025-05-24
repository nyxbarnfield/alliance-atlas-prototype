from flask import Flask, flash, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from forms import FactionForm, CharacterForm
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
    Faction, Character, Relationship,
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
from options.species_options import species_list

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
    user = db.session.get(User, user_id)
    memberships = Membership.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, memberships=memberships)

@app.route('/campaign/<int:campaign_id>')
def campaign_view(campaign_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    user = db.session.get(User, user_id)
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
    form = FactionForm()

    # Always repopulate select options
    form.faction_type.choices = [(val, val) for val in faction_type_list]
    form.alignment.choices = [(val, val) for val in alignment_list]
    form.source.choices = [(val, val) for val in source_list]

    master_factions = MasterFaction.query.all()
    used_names = [f.name for f in campaign.factions]

    if form.validate_on_submit():
        existing = Faction.query.filter(
            func.lower(Faction.name) == form.name.data.strip().lower(),
            Faction.campaign_id == campaign.id
        ).first()
        if existing:
            form.name.errors.append("A faction with that name already exists in this campaign.")
        else:
            new_faction = Faction(
                name=form.name.data.strip(),
                summary=form.summary.data,
                faction_type=form.faction_type.data,
                base_location=form.base_location.data,
                alignment=form.alignment.data,
                leader_name=form.leader_name.data,
                source=form.source.data,
                campaign_id=campaign.id
            )
            db.session.add(new_faction)
            db.session.commit()
            flash("Faction created successfully!", "success")

            if form.skip.data:
                return redirect(url_for('create_character', campaign_id=campaign.id))

            return redirect(url_for('create_faction', campaign_id=campaign.id))  # reload fresh form

    has_factions = len(campaign.factions) > 0
    
    return render_template(
        'create_faction.html',
        campaign=campaign,
        form=form,
        master_factions=master_factions,
        used_names=used_names,
        has_factions=has_factions
    )

    
@app.route('/campaign/<int:campaign_id>/character/new', methods=['GET', 'POST'])
def create_character(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    form = CharacterForm()

    # Populate select fields
    form.species.choices = [(val, val) for val in species_list]
    form.occupation.choices = [(val, val) for val in occupation_list]
    form.age_range.choices = [(val, val) for val in age_range_list]
    form.source.choices = [(val, val) for val in source_list]
    form.faction_id.choices = [(f.id, f.name) for f in campaign.factions]

    if form.validate_on_submit():
        if form.character_type.data == 'NPC':
            character = NPC(
                name=form.name.data.strip(),
                species=form.species.data,
                occupation=form.occupation.data,
                occupation_custom=form.occupation_custom.data,
                age_range=form.age_range.data,
                description=form.description.data,
                source=form.source.data,
                faction_id=form.faction_id.data,
                campaign_id=campaign.id
            )
        else:
            character = Character(
                name=form.name.data.strip(),
                species=form.species.data,
                occupation=form.occupation.data,
                occupation_custom=form.occupation_custom.data,
                age_range=form.age_range.data,
                description=form.description.data,
                source=form.source.data,
                faction_id=form.faction_id.data,
                campaign_id=campaign.id,
                is_claimed=False
            )
        db.session.add(character)
        db.session.commit()
        flash(f'{form.character_type.data} created successfully!', 'success')
        return redirect(url_for('campaign_view', campaign_id=campaign.id))

    return render_template('create_character.html', campaign=campaign, form=form)


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

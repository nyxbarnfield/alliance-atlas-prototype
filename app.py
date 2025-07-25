from flask import Flask, flash, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from forms import FactionForm, CharacterForm, RelationshipForm
import os, random
from constants import EDGE_COLOR_MAP, DEFAULT_FACTION_COLORS
import logging

# --- App & DB Setup ---
app = Flask(__name__)
app.secret_key = "changeme"

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'atlas.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# --- Logging Setup ---

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

# --- Functions ---

def generate_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

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
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    campaigns = [m.campaign for m in user.memberships]

    return render_template('dashboard.html', user=user, campaigns=campaigns)


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
    form.character_type.choices = [("NPC", "NPC"), ("PC", "PC")]

    if form.validate_on_submit():
        # Check for duplicate name in this campaign
        existing = Character.query.filter(
            db.func.lower(Character.name) == form.name.data.strip().lower(),
            Character.campaign_id == campaign.id
        ).first()
        if existing:
            form.name.errors.append("A character with that name already exists in this campaign.")
            return render_template('create_character.html', campaign=campaign, form=form)
        else:
            character = Character(
                name=form.name.data.strip(),
                character_type=form.character_type.data,
                species=form.species.data,
                occupation=form.occupation.data,
                occupation_custom=form.occupation_custom.data or None,
                age_range=form.age_range.data,
                description=form.description.data if form.character_type.data == "NPC" else None,
                source=form.source.data,
                faction_id=form.faction_id.data if form.character_type.data == "NPC" else None,
                campaign_id=campaign.id,
                user_id=None if form.character_type.data == "NPC" else session.get("user_id"),
                is_claimed=False if form.character_type.data == "NPC" else True
            )
            db.session.add(character)
            db.session.commit()
            flash(f'{form.character_type.data} created successfully!', 'success')
            return redirect(url_for('create_character', campaign_id=campaign.id))

    return render_template('create_character.html', campaign=campaign, form=form)



@app.route('/campaign/<int:campaign_id>/claim', methods=['GET', 'POST'])
def claim_pc(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    if request.method == 'POST':
        pc_id = request.form.get("pc_id")
        pc = Character.query.get_or_404(pc_id)
        if pc.is_claimed:
            return "Already claimed", 400
        pc.user_id = user_id
        pc.is_claimed = True
        db.session.commit()
        return redirect(url_for('dashboard'))
    unclaimed_pcs = Character.query.filter_by(campaign_id=campaign.id, is_claimed=False).all()
    return render_template('claim_pc.html', campaign=campaign, unclaimed_pcs=unclaimed_pcs)

@app.route('/campaign/<int:campaign_id>/relationship/new', methods=['GET', 'POST'])
def create_relationship(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    characters = Character.query.filter_by(campaign_id=campaign.id).order_by(Character.name).all()

    form = RelationshipForm()

    # Populate dropdowns
    form.source_id.choices = [(c.id, f"{c.name} ({c.character_type})") for c in characters]
    form.target_id.choices = [(c.id, f"{c.name} ({c.character_type})") for c in characters]
    form.relationship_status.choices = [(val, val.capitalize()) for val in relationship_status_list]
    form.disposition.choices = [(val, val.capitalize()) for val in disposition_list]

    if form.validate_on_submit():
        source_id = int(form.source_id.data)
        target_id = int(form.target_id.data)

        # Prevent self-relationships
        if source_id == target_id:
            form.source_id.errors.append("A character cannot be in a relationship with themselves.")
        else:
            # Check if relationship already exists in either direction
            existing = Relationship.query.filter_by(
                campaign_id=campaign.id,
                source_id=source_id,
                target_id=target_id
            ).first() or Relationship.query.filter_by(
                campaign_id=campaign.id,
                source_id=target_id,
                target_id=source_id
            ).first()

            if existing:
                form.source_id.errors.append("A relationship between these characters already exists.")
            else:
                source_character = Character.query.get(source_id)
                target_character = Character.query.get(target_id)

                relationship = Relationship(
                    source_id=source_character.id,
                    source_type=source_character.character_type,
                    target_id=target_character.id,
                    target_type=target_character.character_type,
                    relationship_status=form.relationship_status.data,
                    disposition=form.disposition.data,
                    description=form.description.data,
                    campaign_id=campaign.id
                )

                db.session.add(relationship)
                db.session.commit()
                flash("Relationship created successfully!", "success")
                return redirect(url_for('create_relationship', campaign_id=campaign.id))

    return render_template(
        'create_relationship.html',
        campaign=campaign,
        form=form
    )

@app.route('/campaign/<int:campaign_id>/diagram')
def view_diagram(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    logger.debug(f"Viewing diagram for campaign: {campaign.name} (ID: {campaign.id})")
    faction_colors = DEFAULT_FACTION_COLORS.copy()

    # Track used colors to avoid duplicates
    used_colors = set(faction_colors.values())

    # Assign random colors to unknown factions
    for faction in campaign.factions:
        logger.debug(f"Processing faction: {faction.name}")
        if faction.name not in faction_colors:
            color = generate_random_color()
            while color in used_colors:
                color = generate_random_color()
            faction_colors[faction.name] = color
            used_colors.add(color)
            logger.debug(f"Assigned new color {color} to faction {faction.name}")

    elements = []
    seen_groups = set()

    # --- Characters → Nodes ---
    for char in campaign.characters:
        if char.character_type == "PC":
            group = "Party"
        elif char.faction:
            group = char.faction.name
        else:
            group = "Unaffiliated"

        # Track group for later parent creation
        seen_groups.add(group)

        logger.debug(f"Adding character: {char.name} | Type: {char.character_type} | Group: {group}")

        elements.append({
            'data': {
                'id': f"char-{char.id}",
                'label': char.name,
                'color': faction_colors.get(char.faction.name if char.faction else None, "#AAAAAA"),
                'parent': group,
                'faction': group,
                'type': char.character_type,
                'species': char.species,
                'occupation': char.occupation,
                'age_range': char.age_range,
                'description': char.description or ""
            }
        })

    # --- Group Containers (Compound Nodes) ---
    for group in seen_groups:
        logger.debug(f"Creating group node: {group}")
        elements.append({
            'data': {
                'id': group,
                'label': group
            }
        })

    # --- Relationships → Edges ---
    for rel in campaign.relationships:
        logger.debug(f"Relationship: {rel.source_id} -> {rel.target_id} | {rel.disposition} ({rel.relationship_status})")
        elements.append({
            'data': {
                'source': f"char-{rel.source_id}",
                'target': f"char-{rel.target_id}",
                'color': EDGE_COLOR_MAP.get(rel.disposition, "#AAAAAA"),
                'disposition': rel.disposition,
                'status': rel.relationship_status
            }
        })
        
    logger.debug(f"Total elements prepared for Cytoscape: {len(elements)}")

    return render_template(
        'view_diagram.html',
        campaign=campaign,
        elements=elements,
        faction_colors=faction_colors,
        edge_colors=EDGE_COLOR_MAP
    )



# --- Run App ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

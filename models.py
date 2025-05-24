from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -- Global Master Templates --

class MasterFaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    summary = db.Column(db.Text)
    alignment = db.Column(db.String(50))
    faction_type = db.Column(db.String(50))
    base_location = db.Column(db.String(100))
    default_leader = db.Column(db.String(100))
    source = db.Column(db.String(100))

class MasterNPC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    species = db.Column(db.String(50))
    occupation = db.Column(db.String(100))
    age_range = db.Column(db.String(50))
    description = db.Column(db.Text)
    source = db.Column(db.String(100))


# -- Core User and Campaign Models --

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    memberships = db.relationship('Membership', backref='user', lazy=True)
    notes = db.relationship('Note', backref='author', lazy=True)
    pcs = db.relationship('PlayerCharacter', backref='owner', lazy=True)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.String(200))
    visibility = db.Column(db.String(20))  # 'public' or 'private'

    memberships = db.relationship('Membership', backref='campaign', lazy=True)
    factions = db.relationship('Faction', backref='campaign', lazy=True)
    npcs = db.relationship('NPC', backref='campaign', lazy=True)
    pcs = db.relationship('PlayerCharacter', backref='campaign', lazy=True)
    relationships = db.relationship('Relationship', backref='campaign', lazy=True)
    notes = db.relationship('Note', backref='campaign', lazy=True)

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'DM' or 'Player'


# -- Factions and Characters --

class Faction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.Text)
    alignment = db.Column(db.String(50))
    base_location = db.Column(db.String(100))
    leader_name = db.Column(db.String(100))
    source = db.Column(db.String(100))
    faction_type = db.Column(db.String(50))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('name', 'campaign_id', name='uq_faction_name_campaign'),
    )

class NPC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50))
    occupation = db.Column(db.String(100))
    age_range = db.Column(db.String(50))
    description = db.Column(db.Text)
    source = db.Column(db.String(100))

    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    faction_id = db.Column(db.Integer, db.ForeignKey('faction.id'), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('name', 'campaign_id', name='uq_npc_name_campaign'),
    )


# -- Player Characters --

class PlayerCharacter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_claimed = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)


# -- Relationships for Diagram --

class Relationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    source_id = db.Column(db.Integer, nullable=False)
    source_type = db.Column(db.String(10), nullable=False)  # 'npc' or 'pc'

    target_id = db.Column(db.Integer, nullable=False)
    target_type = db.Column(db.String(10), nullable=False)

    relationship_status = db.Column(db.String(10), nullable=False)  # 'positive', 'neutral', 'negative'
    disposition = db.Column(db.String(10), nullable=False)  # 'ally', 'enemy', 'unaligned'

    description = db.Column(db.Text)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

    __table_args__ = (
        db.CheckConstraint("relationship_status IN ('positive', 'neutral', 'negative')"),
        db.CheckConstraint("disposition IN ('ally', 'enemy', 'unaligned')"),
    )


# -- Player Notes --

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    character_id = db.Column(db.Integer, nullable=False)
    character_type = db.Column(db.String(10), nullable=False)  # 'npc' or 'pc'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=True)

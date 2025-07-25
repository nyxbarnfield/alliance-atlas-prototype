from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

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
    claimed_characters = db.relationship('Character', backref='user')

    def __repr__(self):
        return f"<User {self.username}>"


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.String(200))
    visibility = db.Column(db.String(20))  # 'public' or 'private'
    characters = db.relationship('Character', backref='campaign', lazy=True)
    memberships = db.relationship('Membership', backref='campaign', lazy=True)
    factions = db.relationship('Faction', backref='campaign', lazy=True)
    relationships = db.relationship('Relationship', backref='campaign', lazy=True)
    notes = db.relationship('Note', backref='campaign', lazy=True)

    def __repr__(self):
        return f"<Campaign {self.name}>"


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

    def __repr__(self):
        return f"<Faction {self.name}>"


class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    character_type = db.Column(db.String(10), nullable=False)  # "NPC" or "PC"
    species = db.Column(db.String(50), nullable=False)
    occupation = db.Column(db.String(100), nullable=False)
    occupation_custom = db.Column(db.String(100), nullable=True)
    age_range = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Only for NPCs
    source = db.Column(db.String(100), nullable=True)
    faction_id = db.Column(db.Integer, db.ForeignKey('faction.id'), nullable=True)
    faction = db.relationship('Faction', backref='characters')
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Only for PCs
    is_claimed = db.Column(db.Boolean, default=False)  # Helpful for PC flow
    
    __table_args__ = (
        db.UniqueConstraint('name', 'campaign_id', name='uq_character_name_campaign'),
    )

    def __repr__(self):
        return f"<Character {self.name} ({self.character_type})>"


# -- Relationships for Diagram --

class Relationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    source_id = db.Column(db.Integer, nullable=False)
    source_type = "character"

    target_id = db.Column(db.Integer, nullable=False)
    target_type = "character"

    relationship_status = db.Column(db.String(10), nullable=False)  # 'positive', 'neutral', 'negative'
    disposition = db.Column(db.String(10), nullable=False)  # 'ally', 'enemy', 'unaligned'

    description = db.Column(db.Text)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

    __table_args__ = (
        db.CheckConstraint("relationship_status IN ('positive', 'neutral', 'negative')"),
        db.CheckConstraint("disposition IN ('ally', 'enemy', 'unaligned')"),
    )

    def __repr__(self):
        return f"<Relationship {self.source_type}-{self.source_id} → {self.target_type}-{self.target_id}>"


# -- Player Notes --

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

    # Relationships for traceability and scoped access
    user = db.relationship('User', back_populates='notes')
    character = db.relationship('Character', back_populates='notes')
    campaign = db.relationship('Campaign', back_populates='notes')

    def __repr__(self):
        """Developer-friendly debug representation."""
        return f"<Note id={self.id} char='{self.character.name}' user='{self.user.username}' priv={self.is_private}>"

    def __str__(self):
        """User-facing friendly description."""
        return f"Note for {self.character.name} by {self.user.username}"

    def __eq__(self, other):
        """Defines equality based on ID and model type."""
        return isinstance(other, Note) and self.id == other.id

    def __hash__(self):
        """Allows use in sets or as dict keys."""
        return hash(self.id)

    def to_dict(self):
        """Serializes the note to a dictionary for APIs or JSON responses."""
        return {
            "id": self.id,
            "content": self.content,
            "character": self.character.name,
            "user": self.user.username,
            "campaign_id": self.campaign_id,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat()
        }
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

class FactionForm(FlaskForm):
    name = StringField('Faction Name', validators=[DataRequired(), Length(max=100)])
    summary = TextAreaField('Summary', validators=[Optional()])
    faction_type = SelectField('Faction Type', choices=[], validators=[DataRequired()])
    base_location = StringField('Base of Operations', validators=[Optional(), Length(max=100)])
    alignment = SelectField('Alignment', choices=[], validators=[DataRequired()])
    leader_name = StringField('Leader Name', validators=[Optional(), Length(max=100)])
    source = SelectField('Source', choices=[], default='Homebrew')

    submit = SubmitField('Create Faction')
    skip = SubmitField('Skip to NPCs')

class CharacterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    species = SelectField('Species', choices=[], validators=[DataRequired()])
    occupation = SelectField('Occupation', choices=[], validators=[DataRequired()])
    occupation_custom = StringField('Other Occupation', validators=[Optional(), Length(max=100)])
    age_range = SelectField('Age Range', choices=[], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    source = SelectField('Source', choices=[], default='Homebrew')
    faction_id = SelectField('Faction', coerce=int, choices=[], validators=[Optional()])
    character_type = SelectField('Character Type', choices=[], validators=[DataRequired()])
    submit = SubmitField('Create Character')
    
class RelationshipForm(FlaskForm):
    source_id = SelectField("Source Character", coerce=int, validators=[DataRequired()])
    target_id = SelectField("Target Character", coerce=int, validators=[DataRequired()])
    relationship_status = SelectField("Status", choices=[
        ("positive", "Positive"),
        ("neutral", "Neutral"),
        ("negative", "Negative")
    ], validators=[DataRequired()])
    disposition = SelectField("Disposition", choices=[
        ("ally", "Ally"),
        ("enemy", "Enemy"),
        ("unaligned", "Unaligned")
    ], validators=[DataRequired()])
    description = TextAreaField("Description (optional)")
    submit = SubmitField("Create Relationship")

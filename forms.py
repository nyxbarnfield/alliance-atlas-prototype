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
    source = StringField('Source (optional)', validators=[Optional(), Length(max=100)])

    submit = SubmitField('Create Faction')
    skip = SubmitField('Skip to NPCs')

class NPCForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    species = SelectField('Species', choices=[], validators=[DataRequired()])
    occupation = SelectField('Occupation', choices=[], validators=[DataRequired()])
    occupation_custom = StringField('Other Occupation', validators=[Optional(), Length(max=100)])
    age_range = SelectField('Age Range', choices=[], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    source = SelectField('Source', choices=[], validators=[Optional()])
    faction_id = SelectField('Faction', coerce=int, choices=[], validators=[Optional()])

    submit = SubmitField('Create NPC')

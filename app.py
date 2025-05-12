from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/atlas.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import models AFTER db init to avoid circular imports
from models import User, Campaign, Membership

# TEMP: Simulate current user (will replace with real auth)
current_user = "nyx"

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    user = User.query.filter_by(username=current_user).first()
    if not user:
        user = User(username=current_user)
        db.session.add(user)
        db.session.commit()

    memberships = Membership.query.filter_by(user_id=user.id).all()
    return render_template('index.html', memberships=memberships, user=user)

@app.route('/campaign/<int:campaign_id>')
def campaign_view(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    user = User.query.filter_by(username=current_user).first()
    membership = Membership.query.filter_by(user_id=user.id, campaign_id=campaign.id).first()

    if membership.role == "DM":
        return render_template('dm_campaign_view.html', campaign_name=campaign.name)
    else:
        return render_template('player_campaign_view.html', campaign_name=campaign.name)

if __name__ == '__main__':
    app.run(debug=True)
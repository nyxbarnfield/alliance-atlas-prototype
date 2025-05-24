from app import app, db
from models import (
    User, Campaign, Membership, Faction, Character,
    MasterFaction, MasterNPC, Relationship, Note
)

def seed_all():
    with app.app_context():
        if Campaign.query.first():
            print("⚠️ Database already seeded. Skipping...")
            return

        # --- Users ---
        dm = User(username="dm_alex")
        player1 = User(username="player_jade")
        player2 = User(username="player_toby")
        db.session.add_all([dm, player1, player2])
        db.session.commit()

        # --- Campaign ---
        campaign = Campaign(
            name="Waterdeep Shadows",
            summary="A tangled web of politics and power.",
            visibility="private"
        )
        db.session.add(campaign)
        db.session.commit()

        # --- Memberships ---
        db.session.add_all([
            Membership(user_id=dm.id, campaign_id=campaign.id, role="DM"),
            Membership(user_id=player1.id, campaign_id=campaign.id, role="Player"),
            Membership(user_id=player2.id, campaign_id=campaign.id, role="Player")
        ])

        # --- Master Factions ---
        zhentarim = MasterFaction(
            name="The Zhentarim",
            summary="A shadowy mercantile group known for smuggling and influence.",
            alignment="Neutral Evil",
            faction_type="Guild",
            base_location="Faerûn",
            default_leader="Davil Starsong",
            source="Waterdeep: Dragon Heist"
        )
        harpers = MasterFaction(
            name="The Harpers",
            summary="Spies and musicians seeking balance and freedom across the realm.",
            alignment="Neutral Good",
            faction_type="Secret Society",
            base_location="Faerûn",
            default_leader="Remallia Haventree",
            source="Player's Handbook"
        )
        db.session.add_all([zhentarim, harpers])

        # --- Master NPCs ---
        db.session.add_all([
            MasterNPC(
                name="Davil Starsong",
                species="Elf",
                occupation="Agent",
                age_range="101–200",
                description="A charming yet dangerous figure from the Zhentarim.",
                source="Waterdeep: Dragon Heist"
            ),
            MasterNPC(
                name="Remallia Haventree",
                species="Half-Elf",
                occupation="Spy",
                age_range="61–100",
                description="A noblewoman and Harper leader with sharp wit and strong ideals.",
                source="Player's Handbook"
            )
        ])

        # --- Campaign Factions ---
        f1 = Faction(
            name="The Zhentarim",
            summary="Smugglers and mercenaries",
            alignment="Neutral Evil",
            faction_type="Guild",
            base_location="Faerûn",
            leader_name="Davil Starsong",
            source="Waterdeep: Dragon Heist",
            campaign_id=campaign.id
        )
        f2 = Faction(
            name="The Harpers",
            summary="Underground resistance of information brokers",
            alignment="Neutral Good",
            faction_type="Secret Society",
            base_location="Faerûn",
            leader_name="Remallia Haventree",
            source="Player's Handbook",
            campaign_id=campaign.id
        )
        db.session.add_all([f1, f2])
        db.session.commit()

        # --- Characters (Unified NPC + PC model) ---
        characters = [
            # NPCs
            Character(
                name="Davil Starsong", character_type="NPC", species="Elf", occupation="Agent",
                age_range="101–200", description="Silver-tongued Zhentarim representative.",
                source="Waterdeep: Dragon Heist", campaign_id=campaign.id, faction_id=f1.id
            ),
            Character(
                name="Remallia Haventree", character_type="NPC", species="Half-Elf", occupation="Spy",
                age_range="61–100", description="Cunning Harper agent and noblewoman.",
                source="Player's Handbook", campaign_id=campaign.id, faction_id=f2.id
            ),
            Character(
                name="Mirt the Moneylender", character_type="NPC", species="Human", occupation="Merchant",
                age_range="61–100", description="Brash, bloated, and brilliant.",
                source="Waterdeep: Dragon Heist", campaign_id=campaign.id, faction_id=f2.id
            ),
            Character(
                name="The Black Viper", character_type="NPC", species="Human", occupation="Thief",
                age_range="31–45", description="Masked noble burglar with unknown allegiance.",
                source="Waterdeep: Dragon Heist", campaign_id=campaign.id
            ),

            # PCs (unclaimed)
            Character(
                name="Kaelen Brightflame", character_type="PC", species="Half-Elf", occupation="Fighter",
                age_range="18–30", source="Homebrew", campaign_id=campaign.id, user_id=None, is_claimed=False
            ),
            Character(
                name="Torrin Dusk", character_type="PC", species="Dragonborn", occupation="Sorcerer",
                age_range="18–30", source="Homebrew", campaign_id=campaign.id, user_id=None, is_claimed=False
            )
        ]
        db.session.add_all(characters)
        db.session.commit()

        # --- Fetch characters for linking ---
        davil = Character.query.filter_by(name="Davil Starsong", campaign_id=campaign.id).first()
        remi = Character.query.filter_by(name="Remallia Haventree", campaign_id=campaign.id).first()
        mirt = Character.query.filter_by(name="Mirt the Moneylender", campaign_id=campaign.id).first()
        viper = Character.query.filter_by(name="The Black Viper", campaign_id=campaign.id).first()

        # --- Relationships ---
        db.session.add_all([
            Relationship(
                source_id=davil.id, source_type="character",
                target_id=remi.id, target_type="character",
                relationship_status="neutral", disposition="ally",
                description="They tolerate each other for the sake of Waterdeep.",
                campaign_id=campaign.id
            ),
            Relationship(
                source_id=mirt.id, source_type="character",
                target_id=viper.id, target_type="character",
                relationship_status="negative", disposition="enemy",
                description="Mirt is actively hunting the Viper for political reasons.",
                campaign_id=campaign.id
            )
        ])

        # --- Notes ---
        db.session.add_all([
            Note(
                character_id=davil.id, character_type="character",
                user_id=dm.id, campaign_id=campaign.id,
                content="DM note: Davil might secretly support the Harpers.",
                is_private=True
            ),
            Note(
                character_id=remi.id, character_type="character",
                user_id=player1.id, campaign_id=campaign.id,
                content="Remallia gave us intel on the Viper.",
                is_private=False
            )
        ])

        db.session.commit()
        print("✅ Sample data seeded successfully.")

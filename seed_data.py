from app import app, db 
from models import (
    User, Campaign, Membership, Faction, NPC,
    PlayerCharacter, MasterFaction, MasterNPC,
    Relationship, Note
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
        campaign = Campaign(name="Waterdeep Shadows", summary="A tangled web of politics and power.", visibility="private")
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

        # --- NPCs ---
        n1 = NPC(name="Davil Starsong", species="Elf", occupation="Agent", age_range="101–200",
                 description="Silver-tongued Zhentarim representative.", source="Waterdeep: Dragon Heist",
                 campaign_id=campaign.id, faction_id=f1.id)
        n2 = NPC(name="Remallia Haventree", species="Half-Elf", occupation="Spy", age_range="61–100",
                 description="Cunning Harper agent and noblewoman.", source="Player's Handbook",
                 campaign_id=campaign.id, faction_id=f2.id)
        n3 = NPC(name="Mirt the Moneylender", species="Human", occupation="Merchant", age_range="61–100",
                 description="Brash, bloated, and brilliant.", source="Waterdeep: Dragon Heist",
                 campaign_id=campaign.id, faction_id=f2.id)
        n4 = NPC(name="The Black Viper", species="Human", occupation="Thief", age_range="31–45",
                 description="Masked noble burglar with unknown allegiance.", source="Waterdeep: Dragon Heist",
                 campaign_id=campaign.id, faction_id=None)

        db.session.add_all([n1, n2, n3, n4])
        db.session.commit()

        # --- Player Characters ---
        pc1 = PlayerCharacter(name="Kaelen Brightflame", is_claimed=False, campaign_id=campaign.id)
        pc2 = PlayerCharacter(name="Torrin Dusk", is_claimed=False, campaign_id=campaign.id)
        db.session.add_all([pc1, pc2])

        # --- Relationships ---
        db.session.add_all([
            Relationship(
                source_id=n1.id, source_type="npc",
                target_id=n2.id, target_type="npc",
                relationship_status="neutral", disposition="ally",
                description="They tolerate each other for the sake of Waterdeep.",
                campaign_id=campaign.id
            ),
            Relationship(
                source_id=n3.id, source_type="npc",
                target_id=n4.id, target_type="npc",
                relationship_status="negative", disposition="enemy",
                description="Mirt is actively hunting the Viper for political reasons.",
                campaign_id=campaign.id
            )
        ])

        # --- Notes ---
        db.session.add_all([
            Note(
                character_id=n1.id, character_type="npc",
                user_id=dm.id, campaign_id=campaign.id,
                content="DM note: Davil might secretly support the Harpers.",
                is_private=True
            ),
            Note(
                character_id=n2.id, character_type="npc",
                user_id=player1.id, campaign_id=campaign.id,
                content="Remallia gave us intel on the Viper.",
                is_private=False
            )
        ])

        db.session.commit()
        print("✅ Sample data seeded successfully.")

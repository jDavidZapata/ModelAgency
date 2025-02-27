from flask.cli import FlaskGroup
from app import create_app
from app.models import db, User, Vote, Model
from app.models_data import models_data


app = create_app()
cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    db.session.add(User(username="juan", password_hash="juan", email="j@j.com"))
    db.session.add(Vote(suggested_name="dave", user_id=1))
    db.session.commit()

@cli.command("seed_db2")
def seed_db2():
    db.session.add(Model(name="Gigi Hadid", password_hash="juan", email="j@j.com",
        image="img/model1.png",
        description="American fashion model, known for her work with Tommy Hilfiger and Victoria's Secret.",
        instagram="gigihadid", 
        height="5'10",
        agency="IMG Models",
        specialization="Fashion Model",
        location="New York",
        experience="High Fashion",
        highlights="walked for Tommy Hilfiger",
        notable_work="Victoria's Secret",
        weight="120 lbs",
        measurements="34-24-34",
        hair_color="Blonde",
        eye_color="Blue",
        media_links="www.example.com"))
    db.session.commit()


@cli.command("seed_db3")
def seed_db3():
    try: # Handle IntegrityError which can occur if name is unique.
        for data in models_data:
            model = Model(**data)
            db.session.add(model)
        db.session.commit()
        print("Database seeded successfully!")
    except Exception as e: # Catch any potential exceptions during seeding.
        db.session.rollback() # rollback session in case of exception.
        print(f"Error seeding database: {e}")



if __name__ == "__main__":
    cli()
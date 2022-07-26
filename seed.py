from models import db, connect_db, User, Feedback
from app import app

# db.drop_all()
db.create_all()

feedbacks = [
    Feedback(title="My first feedback",
             content="OMG, **blushes**", username="Quinn"),
    Feedback(title="More feedback",
             content="OMG, **blushes again**", username="Quinn"),
]
db.session.add_all(feedbacks)
db.session.commit()

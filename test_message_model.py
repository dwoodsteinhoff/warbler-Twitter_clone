import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app


db.create_all()

class UserModelTestCase(TestCase):
    """Test Messages"""

    def setUp(self):
        
        db.drop_all()
        db.create_all()

        user = User.signup("test1", "test1@gmail.com","testpassword", None)
        
        db.session.add(user)
        db.session.commit()

        self.user = User.query.get(1)

        self.client = app.test_client()

    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_message_model(self):
        """Make a message"""
    
        message = Message(
            text="test message",
            user_id = 1
        )

        db.session.add(message)
        db.session.commit()

        # User should have 1 message
        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "test message")

    def test_message_likes(self):

        message1 = Message(
            text="test message 1",
            user_id=1
        )

        message2 = Message(
            text="test message 2",
            user_id=1
        )

        user2 = User.signup("test2", "test2@gmail.com", "testpassword", None)

        db.session.add_all([message1, message2, user2])
        db.session.commit()

        user2.likes.append(message1)

        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == 2).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, message1.id)


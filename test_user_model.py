"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup("test1","test1@gmail.com", "testpassword", None )
        user2 = User.signup("test2","test2@gmail.com", "testpassword", None )

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        user_1 = User.query.get(1)
        user_2 = User.query.get(2)

        self.user1 = user_1
        self.user2 = user_2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    
    def test_user_follows(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user1.following), 1)
        self.assertEqual(len(self.user2.followers), 1)
        self.assertEqual(len(self.user2.following), 0)

        self.assertEqual(self.user1.following[0].id, self.user2.id)
        self.assertEqual(self.user2.followers[0].id, self.user1.id)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertFalse(self.user1.is_followed_by(self.user2))
        self.assertTrue(self.user2.is_followed_by(self.user1))

    def test_valid_signup(self):

        user = User.query.get(1)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "test1")
        self.assertEqual(user.email, "test1@gmail.com")
        self.assertNotEqual(user.password, "testpassword")
        self.assertTrue(user.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        invalid_username = User.signup(None, "test3@gmail.com", "testpassword", None)
        uid = 3
        invalid_username.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid_email = User.signup("test4", None, "testpassword", None)
        uid = 4
        invalid_email.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("test5", "test5@gmail.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("test6", "test6@email.com", None, None)

    def test_valid_authentication(self):
        user = User.authenticate(self.user1.username, "testpassword")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user1.id)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "testpassword"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.user1.username, "badpassword"))


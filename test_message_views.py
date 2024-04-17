"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 1
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_no_session(self):
        with self.client as client:
            resp = client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_invalid_user(self):
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = 435525 

            resp = client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_message_show(self):

        message1 = Message(
            id=1,
            text="test message 5",
            user_id=self.testuser_id
        )
        
        db.session.add(message1)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            message = Message.query.get(1)

            resp = client.get(f'/messages/{message.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(message.text, str(resp.data))

    def test_invalid_message_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/messages/2')

            self.assertEqual(resp.status_code, 500)
    
    def test_message_delete(self):

        message2 = Message(
            id=2,
            text="test message 2",
            user_id=self.testuser_id
        )
        db.session.add(message2)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/2/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            message = Message.query.get(2)
            self.assertIsNone(message)

    def test_unauthorized_message_delete(self):

        user = User.signup(username="unauthorized-user",
                        email="unauthorizedtest@gmail.com",
                        password="testpassword",
                        image_url=None)
        user.id = 50

        message = Message(
            id=3,
            text="a test message",
            user_id=1
        )

        db.session.add_all([user, message])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 50

                resp = c.post("/messages/3/delete", follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized.", str(resp.data))

                the_message = Message.query.get(3)
                self.assertIsNotNone(the_message)

    def test_unauthorized_message_delete(self):

        user = User.signup(username="unauthorized-user",
                        email="unauthorizedtest@gmail.com",
                        password="testpassword",
                        image_url=None)
        user.id = 50

        message = Message(
            id=3,
            text="a test message",
            user_id=1
        )

        db.session.add_all([user, message])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 76543

            resp = c.post("/messages/3/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(3)
            self.assertIsNotNone(m)

    def test_message_delete_no_authentication(self):

        message = Message(
            id=3,
            text="a test message",
            user_id=1
        )

        db.session.add(message)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/3/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(3)
            self.assertIsNotNone(m)

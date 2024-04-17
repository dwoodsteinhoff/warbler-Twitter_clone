import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.user1 = User.signup(username="test1",
                                    email="test1@gmail.com",
                                    password="testpassword",
                                    image_url=None)
        
        self.user1_id = 1
        self.user1.id = self.user1_id

        self.user2 = User.signup("test2", "test2@gmail.com", "testpassword", None)
        self.user2_id = 2
        self.user2.id = self.user2_id

        self.user3 = User.signup("test3", "test3@gmail.com", "testpassword", None)
        self.user3_id = 3
        self.user3.id = self.user3_id

        self.user4 = User.signup("test4", "test4@gmail.com", "password", None)
        self.user4_id = 4
        self.user4.id = self.user4_id

        self.user5 = User.signup("test5", "test5@gmail.com", "password", None)
        self.user5_id = 5
        self.user5.id = self.user5_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_users_index(self):
        with self.client as client:
            resp = client.get("/users")

            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
            self.assertIn("@test4", str(resp.data))
            self.assertIn("@test5", str(resp.data))

    def test_users_search(self):
        with self.client as client:
            resp = client.get("/users?q=test")

            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))            
            self.assertIn("@test3", str(resp.data))
            self.assertIn("@test4", str(resp.data))
            self.assertIn("@test5", str(resp.data))

    def test_user_show(self):
        with self.client as client:
            resp = client.get(f"/users/{self.user1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test1", str(resp.data))


    def test_user_show_with_likes(self):
        message1 = Message(text="message 1", user_id=self.user1_id)
        message2 = Message(text="message 2", user_id=self.user1_id)
        message3 = Message(id=3, text="message 3", user_id=self.user2_id)
        db.session.add_all([message1, message2, message3])
        db.session.commit()

        likes1 = Likes(user_id=self.user1_id, message_id=3)

        db.session.add(likes1)
        db.session.commit()

        with self.client as client:
            resp = client.get(f"/users/{self.user1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test1", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            self.assertIn("2", found[0].text)

            self.assertIn("0", found[1].text)

            self.assertIn("0", found[2].text)

    def test_add_like(self):
        message = Message(id=5, text="message 5", user_id=self.user5_id)
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            resp = c.post("/messages/5/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==5).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.user1_id)

    def test_remove_like(self):
        message1 = Message(text="message 1", user_id=self.user1_id)
        message2 = Message(text="message 2", user_id=self.user1_id)
        message3 = Message(id=3, text="message 3", user_id=self.user2_id)
        db.session.add_all([message1, message2, message3])
        db.session.commit()

        likes1 = Likes(user_id=self.user1_id, message_id=3)

        db.session.add(likes1)
        db.session.commit()

        message = Message.query.filter(Message.text=="message 3").one()
        self.assertIsNotNone(message)
        self.assertNotEqual(message.user_id, self.user1_id)

        likes = Likes.query.filter(
            Likes.user_id==self.user1_id and Likes.message_id==message.id
        ).one()

        self.assertIsNotNone(likes)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            resp = c.post(f"/messages/{message.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes2 = Likes.query.filter(Likes.message_id==message.id).all()

            self.assertEqual(len(likes2), 0)
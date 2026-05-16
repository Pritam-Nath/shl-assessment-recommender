import unittest

from app.models import Message
from app.recommender import SHLAgent


class AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = SHLAgent()

    def test_clarifies_vague_query(self):
        response = self.agent.respond([Message(role="user", content="I need an assessment")])
        self.assertEqual(response.recommendations, [])
        self.assertFalse(response.end_of_conversation)

    def test_recommends_catalog_items(self):
        response = self.agent.respond([Message(role="user", content="Hiring a mid-level Java developer")])
        self.assertGreaterEqual(len(response.recommendations), 1)
        self.assertLessEqual(len(response.recommendations), 10)
        self.assertTrue(all(r.url.startswith("https://www.shl.com/") for r in response.recommendations))

    def test_refuses_off_topic(self):
        response = self.agent.respond([Message(role="user", content="Write legal advice for firing someone")])
        self.assertEqual(response.recommendations, [])
        self.assertIn("SHL assessment", response.reply)

    def test_compares_aliases(self):
        response = self.agent.respond([Message(role="user", content="What is the difference between OPQ and GSA?")])
        self.assertEqual(len(response.recommendations), 2)


if __name__ == "__main__":
    unittest.main()

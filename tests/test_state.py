import os
import tempfile
import unittest

from scraper import load_state, save_state, is_newer


class TestIsNewer(unittest.TestCase):
    def test_no_since_downloads_everything(self):
        self.assertTrue(is_newer("2024-01-01T00:00:00Z", None))
        self.assertTrue(is_newer(None, None))

    def test_strictly_newer_only(self):
        since = "2024-03-05T09:00:00Z"
        self.assertTrue(is_newer("2024-03-05T10:00:00Z", since))
        self.assertFalse(is_newer(since, since))  # equal -> already have it
        self.assertFalse(is_newer("2024-03-01T00:00:00Z", since))

    def test_date_only_since_is_inclusive_of_that_day(self):
        # A full timestamp on the since-day sorts greater than the bare date.
        self.assertTrue(is_newer("2024-01-01T08:00:00Z", "2024-01-01"))

    def test_missing_post_date_is_not_treated_as_old(self):
        self.assertTrue(is_newer(None, "2024-01-01"))


class TestStateRoundTrip(unittest.TestCase):
    def test_missing_state_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_state(d), {})

    def test_save_then_load(self):
        with tempfile.TemporaryDirectory() as d:
            save_state(d, "2024-03-05T09:00:00Z")
            state = load_state(d)
            self.assertEqual(state["latest_post_date"], "2024-03-05T09:00:00Z")
            self.assertIn("last_run", state)

    def test_corrupt_state_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, ".substack_state.json"), "w") as f:
                f.write("{not valid json")
            self.assertEqual(load_state(d), {})


if __name__ == "__main__":
    unittest.main()

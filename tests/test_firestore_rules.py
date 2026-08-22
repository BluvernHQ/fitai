import unittest

try:
    from google.cloud import firestore
except Exception:
    firestore = None


class FirestoreRulesPlaceholder(unittest.TestCase):
    def test_rules_file_exists(self):
        from pathlib import Path
        ui = Path("/Volumes/New buddy/projects/fitai-ui/firestore.rules")
        self.assertTrue(ui.exists())
        text = ui.read_text()
        self.assertIn("allow write: if false", text)

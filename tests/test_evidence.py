import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from vlm_data_doctor import audit
from vlm_data_doctor.report import Report


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def row(self, group="source-1", question="A question"):
        return {"source_id": group, "messages": [{"role": "user", "content": question},
                                                 {"role": "assistant", "content": "An answer"}]}

    def write(self, rows, name="train.jsonl"):
        path = self.root / name
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return path

    def test_group_disjoint_passes(self):
        report = audit(self.write([self.row()]), evaluation=self.write([self.row("source-2", "Other")], "eval.jsonl"), group_key="source_id")
        self.assertEqual(report.issues, [])

    def test_same_group_different_samples_fails(self):
        report = audit(self.write([self.row()]), evaluation=self.write([self.row(question="Other")], "eval.jsonl"), group_key="source_id")
        self.assertEqual([i.code for i in report.issues], ["split_group_overlap"])
        self.assertEqual(report.errors, 1)
        self.assertNotIn("source-1", report.render("json"))

    def test_group_option_is_opt_in(self):
        report = audit(self.write([self.row()]), evaluation=self.write([self.row(question="Other")], "eval.jsonl"))
        self.assertEqual(report.issues, [])

    def test_group_overlap_does_not_hide_exact_sample_overlap(self):
        report = audit(self.write([self.row()]), evaluation=self.write([self.row()], "eval.jsonl"), group_key="source_id")
        self.assertEqual({i.code for i in report.issues}, {"split_group_overlap", "split_sample_overlap"})

    def test_missing_group_is_error(self):
        row = self.row()
        del row["source_id"]
        report = audit(self.write([row]), group_key="source_id")
        self.assertEqual([i.code for i in report.issues], ["invalid_group"])

    def test_bad_groups_are_errors(self):
        for value in [None, True, [], {}, " ", "\ud800"]:
            with self.subTest(value=value):
                report = audit(self.write([self.row(value)]), group_key="source_id")
                self.assertEqual([i.code for i in report.issues], ["invalid_group"])

    def test_group_values_are_type_sensitive(self):
        report = audit(self.write([self.row(1)]), evaluation=self.write([self.row("1", "Other")], "eval.jsonl"), group_key="source_id")
        self.assertEqual(report.issues, [])

    def test_invalid_group_configuration(self):
        for value in ["", " ", 1]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                audit(self.write([self.row()]), group_key=value)

    def test_duplicate_json_keys_are_rejected(self):
        for payload in ['{"messages": [], "messages": []}', '{"outer": {"a": 1, "a": 2}}']:
            path = self.root / "train.jsonl"
            path.write_text(payload, encoding="utf-8")
            self.assertEqual([i.code for i in audit(path).issues], ["invalid_json"])

    def test_duplicate_keys_in_array_file(self):
        path = self.root / "train.json"
        path.write_text('[{"id": 1, "id": 2}]', encoding="utf-8")
        self.assertEqual([i.code for i in audit(path).issues], ["invalid_json"])

    def test_surrogates_are_row_findings_not_crashes(self):
        for field in ["content", "system", "images"]:
            row = self.row()
            if field == "content":
                row["messages"][0]["content"] = "\ud800"
            elif field == "system":
                row["system"] = "\ud800"
            else:
                row["images"] = ["\ud800"]
            with self.subTest(field=field):
                self.assertGreater(audit(self.write([row])).errors, 0)

    def test_manifest_hashes_input_bytes(self):
        path = self.write([self.row()])
        report = audit(path)
        self.assertEqual(report.provenance["dataset_sha256"]["train"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(report.provenance["settings"]["max_pixels"], 40_000_000)
        self.assertNotIn(str(self.root), report.render("json"))

    def test_manifest_changes_with_dataset(self):
        path = self.write([self.row()])
        before = audit(path).provenance["dataset_sha256"]
        self.write([self.row(question="changed")])
        self.assertNotEqual(before, audit(path).provenance["dataset_sha256"])

    def test_manifest_changes_with_image_bytes(self):
        row = self.row(question="<image>Question")
        row["images"] = ["image.png"]
        path = self.write([row])
        Image.new("RGB", (8, 8), "red").save(self.root / "image.png")
        before = audit(path).provenance
        Image.new("RGB", (8, 8), "blue").save(self.root / "image.png")
        after = audit(path).provenance
        self.assertEqual(before["dataset_sha256"], after["dataset_sha256"])
        self.assertNotEqual(before["decoded_image_inventory_sha256"], after["decoded_image_inventory_sha256"])

    def test_report_is_deterministic(self):
        path = self.write([self.row()])
        self.assertEqual(audit(path).to_dict(), audit(path).to_dict())

    def test_html_escapes_every_issue_field(self):
        report = Report(records={"train": 1})
        payload = '<img src=x onerror="alert(1)">'
        report.add("error", payload, payload, 1, payload, payload)
        report.provenance = {"version": payload, "settings": {"group_key": "</pre><script>alert(1)</script>"}}
        output = report.render("html")
        self.assertNotIn(payload, output)
        self.assertNotIn("<script>alert(1)</script>", output)
        self.assertIn("&lt;img", output)
        self.assertIn("Content-Security-Policy", output)

    def test_html_no_remote_assets_or_source_content(self):
        report = audit(self.write([self.row(question="private source text")]))
        html = report.render("html")
        self.assertIn("CHECKS PASSED", html)
        self.assertNotIn("private source text", html)
        self.assertNotIn('src="http', html)
        self.assertNotIn('href="http', html)
        self.assertIn('aria-label="Filter severity"', html)

    def test_html_warning_status(self):
        report = audit(self.write([self.row(), self.row()]))
        self.assertIn("REVIEW WARNINGS", report.render("html"))

    def test_unknown_report_format_rejected(self):
        with self.assertRaises(ValueError):
            Report().render("unsupported")


if __name__ == "__main__":
    unittest.main()

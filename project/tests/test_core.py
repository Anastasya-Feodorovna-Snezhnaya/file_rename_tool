import tempfile
import unittest
from pathlib import Path

from src.core.file_scanner import list_files, scan_sequence
from src.core.rename_engine import RenameOperation, execute_rename_plan
from src.core.rename_rules import get_number_width, make_filename
from src.core.sequence_insert import build_sequence_insert_plan


class FileScannerTests(unittest.TestCase):
    def test_sort_ignores_last_extension_then_uses_extension_as_tiebreaker(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("b.jpg", "a.png", "a.jpg", "a(2).png"):
                (root / name).touch()
            self.assertEqual(
                list_files(temp, "*"),
                ["a.jpg", "a.png", "a(2).png", "b.jpg"]
            )

    def test_sequence_sort_is_numeric_and_keeps_extensions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("part(10).jpg", "part(2).png", "part(1).webp"):
                (root / name).touch()
            found = scan_sequence(temp, "part", "(n)")
            self.assertEqual([item.name for item in found],
                             ["part(1).webp", "part(2).png", "part(10).jpg"])


class NumberingTests(unittest.TestCase):
    def test_fixed_width(self):
        self.assertEqual(get_number_width(11, "fixed", 1, 100), 3)
        self.assertEqual(make_filename("x", "(n)", 1, ".PNG", 3), "x(001).PNG")

    def test_threshold_width_uses_strict_greater_than(self):
        self.assertEqual(get_number_width(50, "threshold", 0, 50), 2)
        self.assertEqual(get_number_width(51, "threshold", 0, 50), 3)
        self.assertEqual(get_number_width(11, "threshold", 0, 100), 2)


class SequenceInsertTests(unittest.TestCase):
    def test_insert_plan_preserves_each_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in (
                "A(01).png", "A(02).jpg", "A(03).png",
                "B(01).webp", "B(02).jpg"
            ):
                (root / name).touch()
            plan = build_sequence_insert_plan(
                temp, "A", "B", "(n)", 1, "out", 1, 2
            )
            self.assertEqual(
                [item.source.name for item in plan],
                ["A(01).png", "B(01).webp", "B(02).jpg",
                 "A(02).jpg", "A(03).png"]
            )
            self.assertEqual(
                [item.target.name for item in plan],
                ["out(01).png", "out(02).webp", "out(03).jpg",
                 "out(04).jpg", "out(05).png"]
            )


class RenameEngineTests(unittest.TestCase):
    def test_two_phase_rename_handles_swapped_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a.txt"
            b = root / "b.txt"
            a.write_text("A", encoding="utf-8")
            b.write_text("B", encoding="utf-8")
            execute_rename_plan([
                RenameOperation(a, b),
                RenameOperation(b, a),
            ])
            self.assertEqual(a.read_text(encoding="utf-8"), "B")
            self.assertEqual(b.read_text(encoding="utf-8"), "A")


if __name__ == "__main__":
    unittest.main()

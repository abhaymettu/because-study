import unittest

from rosterkit.errors import ProjectError
from rosterkit.models import Student
from rosterkit.reader import (
    find_student,
    parse_roster_text,
    parse_student_row,
    read_roster,
    section_names,
)
from tests.support import data_file, full_suite_enabled, generated_roster


class ReadRosterTests(unittest.TestCase):
    def test_reads_sample_file(self):
        students = read_roster(data_file("roster.csv"))
        self.assertEqual(len(students), 5)
        self.assertEqual(
            students[0],
            Student("1001", "Thistle", "Bram", "A", "bthistle@example.edu"),
        )

    def test_blank_email_becomes_none(self):
        students = read_roster(data_file("roster.csv"))
        self.assertIsNone(find_student(students, "1003").email)

    def test_trims_whitespace(self):
        row = {"id": " 7 ", "last_name": "Orrin ", "first_name": " Sol", "section": "C"}
        self.assertEqual(parse_student_row(row), Student("7", "Orrin", "Sol", "C"))

    def test_missing_column_is_rejected(self):
        with self.assertRaises(ProjectError):
            parse_roster_text("id,last_name,section\n1,Orrin,C\n")

    def test_blank_required_value_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_roster_text("id,last_name,first_name,section\n1,Orrin,,C\n")

    def test_duplicate_ids_are_rejected(self):
        text = "id,last_name,first_name,section\n1,Orrin,Sol,C\n1,Varrow,Ines,C\n"
        with self.assertRaises(ValueError):
            parse_roster_text(text)

    @unittest.skipUnless(full_suite_enabled(), "requires ROSTERKIT_ENV=test")
    def test_large_generated_roster(self):
        students = parse_roster_text(generated_roster(2000))
        self.assertEqual(len(students), 2000)
        self.assertEqual(section_names(students), ["A", "B"])


class FindStudentTests(unittest.TestCase):
    def test_unknown_id_raises(self):
        with self.assertRaises(KeyError):
            find_student([], "nobody")

    def test_section_names_are_sorted_and_unique(self):
        students = read_roster(data_file("roster.csv"))
        self.assertEqual(section_names(students), ["A", "B"])

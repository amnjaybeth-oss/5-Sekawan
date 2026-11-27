import math
import os
import tkinter as tk
import traceback
from dataclasses import dataclass
from tkinter import ttk, messagebox

SKS_MIN, SKS_MAX = 1, 6
SCORE_MIN, SCORE_MAX = 0, 100
SEM_MIN, SEM_MAX = 1, 14
MAX_TEXT_LENGTH = 50

GRADE_TABLE = [
    ("A", 85, 4.0),
    ("A-", 80, 3.7),
    ("B+", 75, 3.3),
    ("B", 70, 3.0),
    ("B-", 65, 2.7),
    ("C+", 60, 2.3),
    ("C", 55, 2.0),
    ("D", 40, 1.0),
    ("E", 0, 0.0),
]

class ValidationError(ValueError):
    pass

class AuthError(Exception):
    pass

class Validator:
    @staticmethod
    def check_range(number, field_name, minimum=None, maximum=None):
        if minimum is not None and number < minimum:
            raise ValidationError(f"{field_name} must be at least {minimum:g}.")
        if maximum is not None and number > maximum:
            raise ValidationError(f"{field_name} must be at most {maximum:g}.")

    @staticmethod
    def text(value, field_name, max_length=MAX_TEXT_LENGTH):
        text = str(value).strip()
        if not text:
            raise ValidationError(f"{field_name} cannot be empty.")
        if len(text) > max_length:
            raise ValidationError(f"{field_name} is too long (max {max_length} characters).")
        return text

    @staticmethod
    def integer(value, field_name, minimum=None, maximum=None):
        text = str(value).strip()
        if not text:
            raise ValidationError(f"{field_name} cannot be empty.")
        try:
            number = int(text)
        except ValueError:
            raise ValidationError(f"{field_name} must be a whole number (example: 3).")
        Validator.check_range(number, field_name, minimum, maximum)
        return number

    @staticmethod
    def number(value, field_name, minimum=None, maximum=None):
        text = str(value).strip().replace(",", ".")
        if not text:
            raise ValidationError(f"{field_name} cannot be empty.")
        try:
            number = float(text)
        except ValueError:
            raise ValidationError(f"{field_name} must be a number (example: 78.5).")
        if math.isnan(number) or math.isinf(number):
            raise ValidationError(f"{field_name} must be a real number.")
        Validator.check_range(number, field_name, minimum, maximum)
        return number

    class GradeScale:
    def __init__(self, table=GRADE_TABLE):
        self.table = list(table)

    def score_to_grade(self, score):
        for letter, minimum, points in self.table:
            if score >= minimum:
                return letter, points
        return "E", 0.0

    def minimum_score(self, letter):
        for grade, minimum, _ in self.table:
            if grade == letter:
                return minimum
        raise ValidationError(f"Unknown grade: {letter}")

    def target_letters(self):
        return [letter for letter, _, _ in self.table if letter != "E"]

class GPACalculator:
    def gpa(self, courses):
        total_sks = sum(c.sks for c in courses)
        if total_sks == 0:
            return 0.0
        return sum(c.sks * c.points for c in courses) / total_sks

    def cumulative(self, items):
        total_sks = sum(sks for sks, _ in items)
        if total_sks == 0:
            return 0.0
        return self._weighted_total(items) / total_sks

    def _weighted_total(self, items, index=0):
        if index >= len(items):
            return 0.0
        sks, semester_gpa = items[index]
        return sks * semester_gpa + self._weighted_total(items, index + 1)

@dataclass(frozen=True)
class PlanResult:
    target: str
    minimum: int
    needed: float
    outcome: str

    @property
    def shown(self):
        return math.ceil(self.needed * 10) / 10


class FinalExamPlanner:
    def __init__(self, scale):
        self.scale = scale

    def required_score(self, current_score, final_weight_percent, target_letter):
        if not 0 < final_weight_percent <= 100:
            raise ValidationError("Final exam weight must be between 1 and 100.")
        weight = final_weight_percent / 100
        target = self.scale.minimum_score(target_letter)
        return (target - current_score * (1 - weight)) / weight

    def plan(self, current_score, final_weight_percent, target_letter):
        needed = self.required_score(current_score, final_weight_percent, target_letter)
        if needed > 100:
            outcome = "unreachable"
        elif needed <= 0:
            outcome = "secured"
        else:
            outcome = "reachable"
        return PlanResult(target_letter, self.scale.minimum_score(target_letter), needed, outcome)

class CourseFactory:
    types = {}

    @classmethod
    def register(cls, course_class):
        cls.types[course_class.kind] = course_class
        return course_class

    @classmethod
    def kinds(cls):
        return list(cls.types)

    @classmethod
    def create(cls, kind, name, sks, score, semester=1):
        course_class = cls.types.get(kind)
        if course_class is None:
            raise ValidationError(f"Unknown course type: {kind}")
        return course_class(name, sks, score, semester)


        class Person:
    def __init__(self, name=None, npm=None):
        self.name = name
        self.npm = npm

    def __str__(self):
        return self.name or "Student"
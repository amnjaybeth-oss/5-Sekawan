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

        @CourseFactory.register
class Course:
    kind = "Regular"
    passing_score = 40
    scale = GradeScale()

    def __init__(self, name, sks, score, semester=1):
        self.name = Validator.text(name, "Course name")
        self.sks = sks
        self.score = score
        self.semester = semester

    @property
    def semester(self):
        return self._semester

    @semester.setter
    def semester(self, value):
        Validator.check_range(value, "Semester", SEM_MIN, SEM_MAX)
        self._semester = value

    @property
    def sks(self):
        return self._sks

    @sks.setter
    def sks(self, value):
        Validator.check_range(value, "SKS", SKS_MIN, SKS_MAX)
        self._sks = value

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        Validator.check_range(value, "Score", SCORE_MIN, SCORE_MAX)
        self._score = value

    @property
    def letter(self):
        return self.scale.score_to_grade(self.score)[0]

    @property
    def points(self):
        return self.scale.score_to_grade(self.score)[1]

    def status(self):
        return "Passed" if self.score >= self.passing_score else self.failed_status()

    def failed_status(self):
        return "Retake"

    def describe(self):
        return f"{self.name} ({self.sks} SKS)"

    def __str__(self):
        return self.describe()

@CourseFactory.register
class ElectiveCourse(Course):
    kind = "Elective"

    def failed_status(self):
        return "Replace with another elective"

    def describe(self):
        return f"{self.name} - elective, {self.sks} SKS (can be replaced if failed)"

@CourseFactory.register
class LabCourse(Course):
    kind = "Lab"
    passing_score = 60

    def failed_status(self):
        return f"Retake lab (needs {self.passing_score}+)"

    def describe(self):
        return f"{self.name} - lab/practicum, {self.sks} SKS (pass score {self.passing_score})"

class Semester:
    def __init__(self, number, courses, calculator):
        self.number = number
        self.courses = list(courses)
        self._calculator = calculator

    @property
    def total_sks(self):
        return sum(c.sks for c in self.courses)

    @property
    def gpa(self):
        return self._calculator.gpa(self.courses)

@dataclass(frozen=True)
class SemesterReport:
    number: int
    total_sks: int
    gpa: float | None
    cumulative_gpa: float | None


class Student(Person):
    def __init__(self, name=None, npm=None, calculator=None):
        super().__init__(name, npm)
        self._courses = []
        self._calculator = calculator or GPACalculator()

    @property
    def courses(self):
        return list(self._courses)

    def add_course(self, course):
        if not isinstance(course, Course):
            raise TypeError("Only Course objects can be added.")
        self._courses.append(course)

    def remove_course(self, course):
        if course not in self._courses:
            raise ValidationError("Course was not found.")
        self._courses.remove(course)

    def replace_course(self, old, new):
        if old not in self._courses:
            raise ValidationError("Course to replace was not found.")
        if not isinstance(new, Course):
            raise TypeError("Replacement must be a Course object.")
        self._courses[self._courses.index(old)] = new

    def semesters(self):
        return sorted({c.semester for c in self._courses})

    def courses_in(self, semester):
        return [c for c in self._courses if c.semester == semester]

    def semester_objects(self):
        numbers = self.semesters()
        last = numbers[-1] if numbers else 0
        return [Semester(n, self.courses_in(n), self._calculator) for n in range(1, last + 1)]

    def total_sks(self):
        return sum(c.sks for c in self._courses)

    def gpa(self):
        return self._calculator.gpa(self._courses)

    def semester_report(self):
        history, reports = [], []
        for sem in self.semester_objects():
            history.append((sem.total_sks, sem.gpa))
            has_data = sum(sks for sks, _ in history) > 0
            reports.append(SemesterReport(
                sem.number,
                sem.total_sks,
                sem.gpa if sem.total_sks else None,
                self._calculator.cumulative(history) if has_data else None,
            ))
        return reports

class StudentRepository:
    DEMO_COURSES = [
        ("Regular", "Algoritma dan Pemrograman", 3, 88, 1),
        ("Regular", "Basis Data", 3, 78, 1),
        ("Regular", "Kalkulus", 4, 72, 1),
        ("Regular", "Pemrograman Web", 3, 82, 1),
    ]

    def __init__(self):
        self._students = {}

    def find(self, npm):
        return self._students.get(npm)

    def name_used_by_other_npm(self, name, npm):
        return any(s.name == name and s.npm != npm for s in self._students.values())

    def get_or_create(self, name, npm):
        student = self._students.get(npm)
        if student is None:
            student = Student(name, npm)
            for kind, course_name, sks, score, semester in self.DEMO_COURSES:
                student.add_course(CourseFactory.create(kind, course_name, sks, score, semester))
            self._students[npm] = student
        return student

@dataclass(frozen=True)
class LoginAttempt:
    name: str
    npm: str
    needs_confirmation: bool

class AuthService:
    NPM_LENGTH = 7

    def __init__(self, repository):
        self._repo = repository

    def check(self, raw_name, raw_npm):
        name = Validator.text(raw_name, "Name", max_length=60)
        npm = Validator.text(raw_npm, "NPM", max_length=self.NPM_LENGTH)
        if not all(c.isalpha() or c in " .'-" for c in name):
            raise ValidationError(
                "Name may contain letters, spaces, periods, apostrophes, or hyphens only.")
        if not any(c.isalpha() for c in name):
            raise ValidationError("Name must contain at least one letter.")
        if not npm.isdigit():
            raise ValidationError("NPM must contain numbers only.")
        if len(npm) != self.NPM_LENGTH:
            raise ValidationError(f"NPM must contain exactly {self.NPM_LENGTH} digits.")

        name = name.title()
        registered = self._repo.find(npm)
        if registered and registered.name != name:
            raise AuthError("The name you entered does not match the registered NPM.")
        return LoginAttempt(name, npm, self._repo.name_used_by_other_npm(name, npm))

    def login(self, attempt):
        return self._repo.get_or_create(attempt.name, attempt.npm)

BG = "#F5F7FB"
WHITE = "#FFFFFF"
BLUE = "#1D4ED8"
BLUE_HOVER = "#1E40AF"
BLUE_SOFT = "#E0E7FF"
BLUE_DARK = "#1E3A8A"
TEXT = "#1E293B"
MUTED = "#64748B"
BORDER = "#E2E8F0"
PILL_GRAY = "#EEF1F6"
DANGER = "#DC2626"
SUCCESS = "#15803D"
FAMILY = "Segoe UI"

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")

def font(size, bold=False):
    return (FAMILY, size, "bold" if bold else "normal")

def load_logo(size):
    """Load logo.png (same folder as this script) resized to size x size.
    Returns None if the file is missing or cannot be loaded."""
    if not os.path.exists(LOGO_PATH):
        return None
    try:
        from PIL import Image, ImageTk
        img = Image.open(LOGO_PATH).convert("RGBA")
        img = img.crop(img.getbbox()).resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except ImportError:
        try:
            img = tk.PhotoImage(file=LOGO_PATH)
            return img.subsample(max(1, round(img.width() / size)))
        except tk.TclError:
            return None
    except Exception:
        return None

    class FlatButton(tk.Label):
    def __init__(self, parent, text, command, primary=True):
        self._on_click = command
        self._bg_normal = BLUE if primary else WHITE
        self._bg_hover = BLUE_HOVER if primary else BG
        super().__init__(
            parent, text=text, bg=self._bg_normal,
            fg=WHITE if primary else TEXT,
            font=font(10, True), padx=18, pady=9, cursor="hand2",
            highlightthickness=1,
            highlightbackground=BLUE if primary else BORDER,
        )
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Enter>", lambda e: self.config(bg=self._bg_hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg_normal))

        class ScrollFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, yscrollincrement=30)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._fit)
        self.inner.bind("<Configure>", self._fit)

        self.canvas.bind_all("<MouseWheel>", lambda e: self._move(-1 if e.delta > 0 else 1))
        self.canvas.bind_all("<Button-4>", lambda e: self._move(-1))
        self.canvas.bind_all("<Button-5>", lambda e: self._move(1))

    def _fit(self, event=None):
        self.canvas.itemconfig(self.window, width=self.canvas.winfo_width())
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _move(self, step):
        if not self.canvas.winfo_exists():
            return
        if self.canvas.grab_current() is not None:
            return
        if self.inner.winfo_height() <= self.canvas.winfo_height():
            return
        self.canvas.yview_scroll(step, "units")
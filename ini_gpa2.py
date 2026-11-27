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
        self.canvas.configure(scrol lregion=self.canvas.bbox("all"))

    def _move(self, step):
        if not self.canvas.winfo_exists():
            return
        if self.canvas.grab_current() is not None:
            return
        if self.inner.winfo_height() <= self.canvas.winfo_height():
            return
        self.canvas.yview_scroll(step, "units")

def make_card(parent, bg=WHITE):
    return tk.Frame(parent, bg=bg, highlightbackground=BORDER, highlightthickness=1)

def grade_pill(parent, letter):
    strong = letter in ("A", "A-")
    return tk.Label(
        parent, text=letter, font=font(9, True), padx=10, pady=3,
        bg=BLUE_SOFT if strong else PILL_GRAY,
        fg=BLUE_DARK if strong else "#334155",
    )

def add_field(parent, label, value="", width=32, bg=WHITE):
    tk.Label(parent, text=label, font=font(9, True), bg=bg, fg=MUTED).pack(anchor="w", pady=(10, 4))
    entry = tk.Entry(
        parent, width=width, font=font(11), relief="flat", bg=WHITE, fg=TEXT,
        insertbackground=TEXT, highlightthickness=1,
        highlightbackground=BORDER, highlightcolor=BLUE,
    )
    entry.pack(anchor="w", ipady=6)
    if value != "":
        entry.insert(0, value)
    return entry

def build_table(parent, headers, rows, weights):
    for col, weight in enumerate(weights):
        parent.grid_columnconfigure(col, weight=weight)
    for col, header in enumerate(headers):
        tk.Label(parent, text=header, font=font(9, True), bg=WHITE, fg=MUTED).grid(
            row=0, column=col, sticky="w", pady=(0, 10))
    tk.Frame(parent, bg=BORDER, height=1).grid(row=1, column=0, columnspan=len(headers), sticky="ew")

    if not rows:
        tk.Label(parent, text="No data yet.", font=font(10), bg=WHITE, fg=MUTED).grid(
            row=2, column=0, columnspan=len(headers), sticky="w", pady=16)
        return

    grid_row = 2
    for row in rows:
        for col, cell in enumerate(row):
            if isinstance(cell, tuple) and cell[0] == "pill":
                widget = grade_pill(parent, cell[1])
            elif isinstance(cell, tuple) and cell[0] == "status":
                widget = tk.Label(parent, text=cell[1], font=font(11), bg=WHITE,
                                  fg=TEXT if cell[1] == "Passed" else DANGER)
            elif isinstance(cell, tuple) and cell[0] == "actions":
                widget = tk.Frame(parent, bg=WHITE)
                for text, action in cell[1]:
                    link = tk.Label(widget, text=text, font=font(10, True), bg=WHITE,
                                    fg=DANGER if text == "Delete" else BLUE, cursor="hand2")
                    link.pack(side="left", padx=(0, 14))
                    link.bind("<Button-1>", lambda e, fn=action: fn())
            else:
                widget = tk.Label(parent, text=cell, font=font(11), bg=WHITE, fg=TEXT)
            widget.grid(row=grid_row, column=col, sticky="w", pady=13)
        tk.Frame(parent, bg=BORDER, height=1).grid(
            row=grid_row + 1, column=0, columnspan=len(headers), sticky="ew")
        grid_row += 2

class CourseDialog(tk.Toplevel):
    def __init__(self, parent, on_save, course=None):
        super().__init__(parent, bg=WHITE)
        self.title("Edit Course" if course else "Add Course")
        self.resizable(False, False)
        self._on_save = on_save

        body = tk.Frame(self, bg=WHITE, padx=28, pady=24)
        body.pack()
        tk.Label(body, text="Edit Course" if course else "Add Course",
                 font=font(15, True), bg=WHITE, fg=TEXT).pack(anchor="w")

        self.e_name = add_field(body, "Course name", course.name if course else "")
        self.e_sks = add_field(body, f"SKS ({SKS_MIN}-{SKS_MAX})", course.sks if course else "", width=12)
        self.e_score = add_field(body, f"Score ({SCORE_MIN}-{SCORE_MAX})", f"{course.score:g}" if course else "", width=12)
        self.e_sem = add_field(body, f"Semester ({SEM_MIN}-{SEM_MAX})", course.semester if course else 1, width=12)

        tk.Label(body, text="Type", font=font(9, True), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(10, 4))
        self.cb_kind = ttk.Combobox(body, state="readonly", width=12, font=font(11),
                                    values=CourseFactory.kinds())
        self.cb_kind.set(course.kind if course else "Regular")
        self.cb_kind.pack(anchor="w", ipady=4)
        self.cb_kind.bind("<MouseWheel>", lambda e: "break")

        self.error = tk.Label(body, text="", font=font(9), bg=WHITE, fg=DANGER,
                              wraplength=320, justify="left")
        self.error.pack(anchor="w", pady=(12, 0))

        buttons = tk.Frame(body, bg=WHITE)
        buttons.pack(fill="x", pady=(14, 0))
        FlatButton(buttons, "Save", self._save).pack(side="right")
        FlatButton(buttons, "Cancel", self.destroy, primary=False).pack(side="right", padx=(0, 10))

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent.winfo_toplevel())
        self.wait_visibility()
        self.grab_set()
        self.e_name.focus_set()

        def _save(self):
        try:
            name = Validator.text(self.e_name.get(), "Course name")
            sks = Validator.integer(self.e_sks.get(), "SKS", SKS_MIN, SKS_MAX)
            score = Validator.number(self.e_score.get(), "Score", SCORE_MIN, SCORE_MAX)
            semester = Validator.integer(self.e_sem.get(), "Semester", SEM_MIN, SEM_MAX)
            self._on_save(name, sks, score, semester, self.cb_kind.get())
        except (ValueError, TypeError) as err:
            self.error.config(text=str(err))
            return
        self.destroy()

class BasePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    @property
    def student(self):
        return self.app.student

    def refresh(self, keep_scroll=False):
        position = 0.0
        if keep_scroll and getattr(self, "scroll", None) is not None:
            position = self.scroll.canvas.yview()[0]
        for child in self.winfo_children():
            child.destroy()
        self.build()
        if position:
            self.after(30, lambda: self._restore_scroll(position))

    def _restore_scroll(self, position):
        if self.scroll.canvas.winfo_exists():
            self.scroll.canvas.yview_moveto(position)

    def build(self):
        raise NotImplementedError

    def container(self):
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)
        box = tk.Frame(self.scroll.inner, bg=BG)
        box.pack(fill="both", expand=True, padx=60, pady=30)
        return box

    def heading(self, parent, title, subtitle=""):
        tk.Label(parent, text=title, font=font(24, True), bg=BG, fg=TEXT).pack(anchor="w")
        if subtitle:
            tk.Label(parent, text=subtitle, font=font(11), bg=BG, fg=MUTED).pack(anchor="w")

class HomePage(BasePage):
    def build(self):
        box = self.container()
        title = f"Hi, {self.student.name}!" if self.student.name else "Summary"
        self.heading(box, title, "Here is a summary of your semester.")

        stats = tk.Frame(box, bg=BG)
        stats.pack(fill="x", pady=(18, 18))
        for i in range(3):
            stats.grid_columnconfigure(i, weight=1, uniform="stat")
        self._stat(stats, 0, "Your GPA", f"{self.student.gpa():.2f}", highlight=True)
        self._stat(stats, 1, "Total SKS", str(self.student.total_sks()))
        self._stat(stats, 2, "Courses", str(len(self.student.courses)))

        card = make_card(box)
        card.pack(fill="both", expand=True)
        inner = tk.Frame(card, bg=WHITE, padx=24, pady=22)
        inner.pack(fill="both", expand=True)
        head = tk.Frame(inner, bg=WHITE)
        head.pack(fill="x", pady=(0, 16))
        tk.Label(head, text="My Courses", font=font(14, True), bg=WHITE, fg=TEXT).pack(side="left")
        FlatButton(head, "Add Course", self.app.open_course_dialog).pack(side="right")

        table = tk.Frame(inner, bg=WHITE)
        table.pack(fill="x")
        rows = [[c.name, str(c.sks), f"{c.score:g}", ("pill", c.letter)] for c in self.student.courses]
        build_table(table, ["Course", "SKS", "Score", "Grade"], rows, [5, 2, 2, 2])

    def _stat(self, parent, col, label, value, highlight=False):
        bg = BLUE if highlight else WHITE
        card = tk.Frame(parent, bg=bg, highlightbackground=BLUE if highlight else BORDER,
                        highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=(0, 14) if col < 2 else 0)
        tk.Label(card, text=label, font=font(10, highlight), bg=bg,
                 fg=WHITE if highlight else MUTED).pack(anchor="w", padx=24, pady=(22, 0))
        tk.Label(card, text=value, font=font(34, True), bg=bg,
                 fg=WHITE if highlight else TEXT).pack(anchor="w", padx=24, pady=(4, 22))

class CoursesPage(BasePage):
    def build(self):
        box = self.container()
        top = tk.Frame(box, bg=BG)
        top.pack(fill="x")
        left = tk.Frame(top, bg=BG)
        left.pack(side="left")
        self.heading(left, "Courses", "Add, edit or remove your courses.")
        FlatButton(top, "Add Course", self.app.open_course_dialog).pack(side="right", anchor="s")

        card = make_card(box)
        card.pack(fill="x", pady=(18, 0))
        table = tk.Frame(card, bg=WHITE, padx=24, pady=20)
        table.pack(fill="x")
        rows = []
        for course in self.student.courses:
            actions = ("actions", [
                ("Edit", lambda c=course: self.app.open_course_dialog(c)),
                ("Delete", lambda c=course: self._delete(c)),
            ])
            rows.append([course.name, course.kind, str(course.sks), f"{course.score:g}",
                         ("pill", course.letter), ("status", course.status()), str(course.semester), actions])
        build_table(table, ["Course", "Type", "SKS", "Score", "Grade", "Status", "Semester", ""], rows,
                    [5, 2, 1, 1, 1, 4, 1, 2])

    def _delete(self, course):
        if messagebox.askyesno("Delete course", f"Delete {course.describe()}?"):
            self.student.remove_course(course)
            self.app.shell.refresh()

class PlannerPage(BasePage):
    def build(self):
        box = self.container()
        self.heading(box, "Planner", "Find the final exam score you need for a target grade.")

        card = make_card(box)
        card.pack(fill="x", pady=(18, 0))
        inner = tk.Frame(card, bg=WHITE, padx=28, pady=24)
        inner.pack(fill="x")
        tk.Label(inner, text="What do I need?", font=font(14, True), bg=WHITE, fg=TEXT).pack(anchor="w")

        form = tk.Frame(inner, bg=WHITE)
        form.pack(anchor="w", pady=(4, 0))
        col1 = tk.Frame(form, bg=WHITE)
        col1.grid(row=0, column=0, padx=(0, 24), sticky="n")
        col2 = tk.Frame(form, bg=WHITE)
        col2.grid(row=0, column=1, padx=(0, 24), sticky="n")
        col3 = tk.Frame(form, bg=WHITE)
        col3.grid(row=0, column=2, sticky="n")

        self.e_current = add_field(col1, "Score so far, before the final exam (0-100)", width=30)
        self.e_weight = add_field(col2, "Final exam weight (%)", "40", width=22)
        tk.Label(col3, text="Target grade", font=font(9, True), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(10, 4))
        self.cb_target = ttk.Combobox(col3, state="readonly", width=8, font=font(11),
                                      values=self.app.scale.target_letters())
        self.cb_target.set("A")
        self.cb_target.pack(anchor="w", ipady=4)
        self.cb_target.bind("<MouseWheel>", lambda e: "break")

        FlatButton(inner, "Calculate", self._calculate).pack(anchor="w", pady=(20, 0))
        self.result = tk.Label(inner, text="", font=font(22, True), bg=WHITE, fg=TEXT)
        self.result.pack(anchor="w", pady=(20, 0))
        self.detail = tk.Label(inner, text="", font=font(10), bg=WHITE, fg=MUTED,
                               wraplength=640, justify="left")
        self.detail.pack(anchor="w", pady=(2, 0))

    def _calculate(self):
        try:
            current = Validator.number(self.e_current.get(), "Score so far", 0, 100)
            weight = Validator.number(self.e_weight.get(), "Final exam weight", 1, 100)
            target = self.cb_target.get()
            if not target:
                raise ValidationError("Please choose a target grade.")
            plan = self.app.planner.plan(current, weight, target)
        except ValueError as err:
            self.result.config(text="", fg=TEXT)
            self.detail.config(text=str(err), fg=DANGER)
            return

        if plan.outcome == "unreachable":
            self.result.config(text=f"{plan.shown:.1f}", fg=DANGER)
            self.detail.config(fg=MUTED, text=f"Not reachable: grade {plan.target} needs more than 100 on the final exam.")
        elif plan.outcome == "secured":
            self.result.config(text="Already secured", fg=SUCCESS)
            self.detail.config(fg=MUTED, text=f"You already have enough for grade {plan.target}, even with a 0 on the final.")
        else:
            self.result.config(text=f"{plan.shown:.1f}", fg=BLUE)
            self.detail.config(fg=MUTED, text=f"Score needed on the final exam to get {plan.target} (minimum total {plan.minimum}).")

class GradesPage(BasePage):
    def build(self):
        box = self.container()
        self.heading(box, "Grades", "Grade conversion and your GPA per semester.")

        grid = tk.Frame(box, bg=BG)
        grid.pack(fill="x", pady=(18, 0))
        grid.grid_columnconfigure(0, weight=2, uniform="g")
        grid.grid_columnconfigure(1, weight=3, uniform="g")

        left = make_card(grid)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left_in = tk.Frame(left, bg=WHITE, padx=24, pady=22)
        left_in.pack(fill="both", expand=True)
        tk.Label(left_in, text="Grade Conversion", font=font(14, True), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(0, 14))
        table1 = tk.Frame(left_in, bg=WHITE)
        table1.pack(fill="x")
        rows1 = [[("pill", letter), f"{minimum}+", f"{points:.1f}"]
                 for letter, minimum, points in self.app.scale.table]
        build_table(table1, ["Grade", "Min score", "Points"], rows1, [1, 1, 1])

        right = make_card(grid)
        right.grid(row=0, column=1, sticky="nsew")
        right_in = tk.Frame(right, bg=WHITE, padx=24, pady=22)
        right_in.pack(fill="both", expand=True)
        tk.Label(right_in, text="GPA per Semester", font=font(14, True), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(0, 14))
        table2 = tk.Frame(right_in, bg=WHITE)
        table2.pack(fill="x")
        rows2 = [[f"Semester {r.number}", str(r.total_sks),
                  f"{r.gpa:.2f}" if r.gpa is not None else "-",
                  f"{r.cumulative_gpa:.2f}" if r.cumulative_gpa is not None else "-"]
                 for r in self.student.semester_report()]
        build_table(table2, ["Semester", "SKS", "GPA", "Cumulative GPA"], rows2, [2, 1, 1, 2])

class Shell(tk.Frame):
    PAGES = [
        ("home", "Home", HomePage),
        ("courses", "Courses", CoursesPage),
        ("planner", "Planner", PlannerPage),
        ("grades", "Grades", GradesPage),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.current = "home"
        self.nav_items = {}
        self._build_navbar()

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.pages = {}
        for key, _, page_class in self.PAGES:
            page = page_class(self.content, app)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page
        self.show("home")

    def _build_navbar(self):
        bar = tk.Frame(self, bg=WHITE)
        bar.pack(fill="x")
        inner = tk.Frame(bar, bg=WHITE)
        inner.pack(fill="x", padx=60, pady=14)

        self.logo_img = load_logo(36)
        if self.logo_img:
            tk.Label(inner, image=self.logo_img, bg=WHITE).pack(side="left")
        else:
            tk.Label(inner, text="GP", font=font(11, True), bg=BLUE, fg=WHITE,
                     width=3, pady=6).pack(side="left")
        tk.Label(inner, text="GPA Planner", font=font(13, True), bg=WHITE, fg=TEXT).pack(side="left", padx=(10, 24))

        for key, label, _ in self.PAGES:
            item = tk.Label(inner, text=label, font=font(10, True), bg=WHITE, fg=MUTED,
                            padx=16, pady=8, cursor="hand2")
            item.pack(side="left", padx=2)
            item.bind("<Button-1>", lambda e, k=key: self.show(k))
            self.nav_items[key] = item

        FlatButton(inner, "Logout", self.app.show_login, primary=False).pack(side="right")

        if self.app.student.name:
            info = tk.Frame(inner, bg=WHITE)
            info.pack(side="right", padx=(0, 14))
            tk.Label(info, text=self.app.student.name, font=font(10, True), bg=WHITE, fg=TEXT).pack(anchor="e")
            if self.app.student.npm:
                tk.Label(info, text=f"NPM {self.app.student.npm}", font=font(9), bg=WHITE, fg=MUTED).pack(anchor="e")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def show(self, key):
        self.current = key
        for k, item in self.nav_items.items():
            active = k == key
            item.config(bg=BLUE_SOFT if active else WHITE, fg=BLUE_DARK if active else MUTED)
        page = self.pages[key]
        page.refresh()
        page.tkraise()

    def refresh(self):
        self.pages[self.current].refresh(keep_scroll=True)

class LoginScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        box = tk.Frame(self, bg=WHITE, padx=42, pady=36,
                       highlightbackground=BORDER, highlightthickness=1)
        box.place(relx=0.5, rely=0.5, anchor="center")

        self.logo_img = load_logo(80)
        if self.logo_img:
            tk.Label(box, image=self.logo_img, bg=WHITE).pack(pady=(0, 14))

        tk.Label(box, text="STUDENT LOGIN", font=font(22, True),
                 bg=WHITE, fg=BLUE_DARK).pack(pady=(0, 8))
        tk.Label(box, text="Enter your name and NPM to continue",
                 font=font(10), bg=WHITE, fg=MUTED).pack(pady=(0, 22))

        self.e_nama = add_field(box, "Full name", width=32)
        self.e_npm = add_field(box, f"NPM ({AuthService.NPM_LENGTH} digits)", width=32)

        self.error = tk.Label(box, text="", font=font(9), bg=WHITE,
                              fg=DANGER, wraplength=300, justify="left")
        self.error.pack(anchor="w", pady=(10, 0))

        FlatButton(box, "Login", self.proses_login).pack(fill="x", pady=(18, 0))

        self.e_nama.bind("<Return>", lambda e: self.proses_login())
        self.e_npm.bind("<Return>", lambda e: self.proses_login())
        self.e_nama.focus_set()

    def proses_login(self):
        try:
            attempt = self.app.auth.check(self.e_nama.get(), self.e_npm.get())
        except (ValueError, AuthError) as err:
            self.error.config(text=str(err))
            return
        if attempt.needs_confirmation and not messagebox.askyesno(
                "Confirm NPM",
                "This name is already registered with a different NPM. "
                "Is the NPM you entered correct?"):
            return
        self.app.show_main(attempt)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Login - GPA Planner")
        self.geometry("1100x760")
        self.minsize(900, 640)
        self.configure(bg=BG)

        self._icon = load_logo(64)
        if self._icon:
            try:
                self.iconphoto(True, self._icon)
            except tk.TclError:
                pass  

        self.student = None
        self.shell = None
        self.scale = Course.scale
        self.planner = FinalExamPlanner(self.scale)
        self.repository = StudentRepository()
        self.auth = AuthService(self.repository)

        try:
            ttk.Style().theme_use("clam")
        except tk.TclError:
            pass

        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
        self.show_login()

    def toggle_fullscreen(self, event=None):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def exit_fullscreen(self, event=None):
        self.attributes("-fullscreen", False)

    def report_callback_exception(self, exc_type, exc_value, exc_tb):
        traceback.print_exception(exc_type, exc_value, exc_tb)
        messagebox.showerror("Unexpected error", f"{exc_typ
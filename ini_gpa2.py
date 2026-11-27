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
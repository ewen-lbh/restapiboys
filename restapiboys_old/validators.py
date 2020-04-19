from restapiboys.utils import get_path
from typing import Callable, Any
import importlib
import datetime

class TypeValidator: 
  def __init__(self, _type: str) -> Callable[[Any], bool]:
    try:
      validator = getattr(self, _type)
    except AttributeError:
      raise ValueError(f"Type {_type} does not exist")
    return validator
  
  @staticmethod
  def integer(value) -> bool:
    return type(value) is int

  @staticmethod
  def number(value) -> bool:
    return type(value) is float
    
  @staticmethod
  def string(value) -> bool:
    return type(value) is str

  @staticmethod
  def boolean(value) -> bool:
    return type(value) is bool

  @staticmethod
  def datetime(value) -> bool:
    try:
      datetime.datetime.fromisoformat(value)
      return True
    except ValueError:
      return False
    
  @staticmethod
  def date(value) -> bool:
    try:
      datetime.date.fromisoformat(value)
      return True
    except ValueError:
      return False

  @staticmethod
  def date(value) -> bool:
    try:
      datetime.time.fromisoformat(value)
      return True
    except ValueError:
      return False

def required_validator(response: dict, key) -> bool:
  return key in response.keys()

def max_length(value: str, max_length: int) -> bool:
  return len(value) <= max_length

def min_length(value: str, max_length: int) -> bool:
  return len(value) >= max_length

class CustomValidator:
  def __init__(self, validation_string) -> Callable[Any, bool]:
    self.validation_string = validation_string
    return self.execute_with_locals
    
  def execute_with_locals(self, value) -> bool:
    # Assing the "placeholder"
    _ = value
    # Import functions from the users's "validators.py"
    with open(get_path('validators.py'), 'r') as file:
      exec(file.read())
    # Prevent use of global variables
    globs = {}
    locs = locals()
    return bool(exec(self.validation_string, globs, locs))

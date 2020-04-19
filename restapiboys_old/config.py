from typing import Dict, Any
import re
from utils import yaml, get_path

class Config:
  _ACCEPTABLE_KEYS_PATTERN = re.compile(r'[a-bA-B_][\w_]*')
  KEY_SUBSTITUTE_CHARACTER = '_'
  DEFAULT_CONFIG = {
    'authentification': 'jwt',
    'users': {
      'fields': ['email', 'password', 'joined_at', 'logged_at'],
      'verify accounts via': 'email',
      'reset passwords via': 'email'
    },
    'domain name': None,
    'https': True
  }
  
  def __init__(self, filepath: str):
    self._filepath = filepath
    self._full_filepath = get_path(filepath)
    # Parse YAML stream
    self._dict = yaml.load_file(self._full_filepath)
    # Normalize keys
    self._dict = self._normalize_keys(self._dict)
    # Add defaults
    self._dict = { **self.DEFAULT_CONFIG, **self._dict }
    # Remove unknown keys
    self._dict = self._remove_unknown_keys(self._dict, self.DEFAULT_CONFIG)
  
  def __iter__(self):
    for key, value in self._dict.items():
      yield key, value
    
  def keys(self):
    return list(self._dict.keys())
  
  def __getitem__(self):
    return 
  
  @classmethod
  def _remove_unknown_keys(cls, o: dict, keys_schema: Dict[str, Any]) -> dict:
    no_unknowns = {}
    for key, value in o.items():
      if key in keys_schema.keys():
        if type(value) is dict:
          no_unknowns[key] = cls._remove_unknown_keys(value, keys_schema[key])
        else:
          no_unknowns[key] = value
    return no_unknowns
  
  @classmethod
  def _normalize_key(cls, key: str) -> str:
    normalized_key = ""
    for c in key:
      if not cls._ACCEPTABLE_KEYS_PATTERN.match(c):
        c = cls.KEY_SUBSTITUTE_CHARACTER
      key += c
    return normalized_key
      
  @classmethod
  def _normalize_keys(cls, o: dict) -> dict:
    normalized_dict = {}
    for key, value in o.items():
      key = cls._normalize_key(key)
      if type(value) is dict:
        normalized_dict[key] = cls._normalize_keys(value)
      else:
        normalized_dict[key] = value
    return normalized_dict

"""
Common utilities
"""
from typing import Any, Dict, NamedTuple
import yaml as pyyaml
import os
import collections

class ExecYAMLTag(pyyaml.YAMLObject):
  yaml_tag = u'!exec'
  
  def __init__(self, code):
    self.code = code
  
  def __repr__(self):
    return 'ExecTag({})'.format(self.code)
  
  @classmethod
  def from_yaml(cls, loader, node):
    return ExecYAMLTag(node.value)
  
  @classmethod
  def to_yaml(cls, dumper, data):
    return dumper.represent_scalar(cls.yaml_tag, data.env_var)

pyyaml.SafeLoader.add_constructor('!exec', ExecYAMLTag.from_yaml)
pyyaml.SafeDumper.add_multi_representer(ExecYAMLTag, ExecYAMLTag.to_yaml)

class yaml:
  @staticmethod
  def loads(stream: str) -> Dict[str, Any]:
    loaded = pyyaml.load(stream, Loader=pyyaml.SafeLoader)
    if type(loaded) is not dict:
      raise ValueError(f"The provided YAML stream does not define a dict")
    return loaded

  @classmethod
  def load_file(cls: 'yaml', filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r') as file:
      stream: str = file.read()
    try:
      return cls.loads(stream)
    except Exception as e:
      print(f"Something went wrong while parsing YAML file {filepath}:", e)
  
  @staticmethod
  def dumps(obj: Any) -> str:
    return pyyaml.dump(obj, default_flow_style=True, allow_unicode=True, Dumper=pyyaml.SafeDumper)
    
  @classmethod
  def dump_file(cls: 'yaml', obj: Any, filepath: str) -> None:
    with open(filepath, 'w') as file:
      stream: str = cls.dumps(obj)
      file.write(stream)


def get_path(*fragments: str) -> str:
  return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'example', 'src', *fragments))


def recursive_namedtuple_to_dict(obj: NamedTuple) -> dict:
  as_dict = {}
  for key, value in dict(obj._asdict()).items():
    if isinstance_namedtuple(value):
      value = recursive_namedtuple_to_dict(value)
    as_dict[key] = value
  return as_dict

def isinstance_namedtuple(obj: Any) -> bool:
  return hasattr(obj, '_asdict') and obj._asdict.__doc__ == 'Return a new OrderedDict which maps field names to their values.'

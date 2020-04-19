"""
Common utilities
"""
from typing import Any, Dict, NamedTuple
import os
import keyword
import warnings
import re
import yaml as pyyaml


class ExecYAMLTag(pyyaml.YAMLObject):
    yaml_tag = "!exec"

    def __init__(self, code):
        self.code = code

    def __repr__(self):
        return "ExecTag({})".format(self.code)

    @classmethod
    def from_yaml(cls, loader, node):
        return ExecYAMLTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.env_var)


pyyaml.SafeLoader.add_constructor("!exec", ExecYAMLTag.from_yaml)
pyyaml.SafeDumper.add_multi_representer(ExecYAMLTag, ExecYAMLTag.to_yaml)


class yaml:
    @staticmethod
    def loads(stream: str) -> Dict[str, Any]:
        loaded = pyyaml.load(stream, Loader=pyyaml.SafeLoader)
        if type(loaded) is not dict:
            raise ValueError(f"The provided YAML stream does not define a dict")
        return loaded

    @classmethod
    def load_file(cls: "yaml", filepath: str) -> Dict[str, Any]:
        with open(filepath, "r") as file:
            stream: str = file.read()
        try:
            return cls.loads(stream)
        except Exception as e:
            print(f"Something went wrong while parsing YAML file {filepath}:", e)

    @staticmethod
    def dumps(obj: Any) -> str:
        return pyyaml.dump(
            obj, default_flow_style=True, allow_unicode=True, Dumper=pyyaml.SafeDumper
        )

    @classmethod
    def dump_file(cls: "yaml", obj: Any, filepath: str) -> None:
        with open(filepath, "w") as file:
            stream: str = cls.dumps(obj)
            file.write(stream)


def get_path(*fragments: str) -> str:
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "example", "src", *fragments)
    )


def recursive_namedtuple_to_dict(obj: NamedTuple) -> dict:
    as_dict = {}
    for key, value in dict(obj._asdict()).items():
        if isinstance_namedtuple(value):
            value = recursive_namedtuple_to_dict(value)
        as_dict[key] = value
    return as_dict


def isinstance_namedtuple(obj: Any) -> bool:
    return (
        hasattr(obj, "_asdict")
        and obj._asdict.__doc__
        == "Return a new OrderedDict which maps field names to their values."
    )


def string_to_identifier(string: str) -> str:
    # Replace invalid characters with an underscore
    string = re.sub(r"[^0-9a-zA-Z_]", "_", string)

    # Remove leading characters until we find a letter or underscore
    string = re.sub(r"^[^a-zA-Z]+", "", string)

    # Check if its not a python keyword.
    # If it is, add a '_' in front.
    if keyword.iskeyword(string):
        warnings.warn(
            f"{string!r} conflicts with a python keyword. Reference it in python code with {'_'+string!r}'"
        )
        string = "_" + string

    return string

def replace_whitespace_in_keys(obj: Dict[str, Any], sub: str = '_') -> Dict[str, Any]:
    """
    Removes whitespace from dict keys
    
    :param sub: Replace whitespace characters with this
    :param obj: The dictionnary to replace keys in
    """
    normalized = {}
    PATTERN = re.compile(r"")
    for key, value in obj.items():
        key = re.sub(r"\s", sub, key)
        normalized[key] = value
    return normalized

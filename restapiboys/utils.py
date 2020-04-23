"""
Common utilities
"""
from typing import *
from restapiboys import log
import os
import keyword
import warnings
import re
import yaml as pyyaml


class PythonCodeYAMLTag(pyyaml.YAMLObject):
    yaml_tag = "!run"

    def __init__(self, code):
        self.code = code

    def __repr__(self):
        return "PythonCode({})".format(self.code)

    @classmethod
    def from_yaml(cls, loader, node):
        return PythonCodeYAMLTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.env_var)


class yaml:
    @staticmethod
    def loads(
        stream: str, multiple_documents: bool = False
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        pyyaml.SafeLoader.add_constructor("!run", PythonCodeYAMLTag.from_yaml)
        pyyaml.SafeDumper.add_multi_representer(
            PythonCodeYAMLTag, PythonCodeYAMLTag.to_yaml
        )
        if multiple_documents:
            loaded = list(pyyaml.load_all(stream, Loader=pyyaml.SafeLoader))
        else:
            loaded = pyyaml.load(stream, Loader=pyyaml.SafeLoader)
        if type(loaded) is not dict and not multiple_documents:
            raise ValueError(f"The provided YAML stream does not define a dict")
        return loaded

    @classmethod
    def load_file(
        cls, filepath: str, multiple_documents=False
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        with open(filepath, "r") as file:
            stream: str = file.read()
        try:
            return cls.loads(stream, multiple_documents)
        except Exception as e:
            # print(f"Something went wrong while parsing YAML file {filepath}:")
            raise e

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


# TODO: Detect instead of hardcoding it
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


def replace_whitespace_in_keys(obj: Dict[str, Any], sub: str = "_") -> Dict[str, Any]:
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


def is_list_uniformely_typed(obj: list) -> bool:
    """
    Checks if the given list has all of its elements
    of the same type
    """
    if len(obj) < 1:
        return None

    first_element_type = type(obj[0])
    return all([type(el) is first_element_type for el in obj])

def resolve_synonyms_to_primary(synonyms_map: Dict[str, List[str]], string: str) -> Optional[str]:
    """
    Let _k_ be the keys of `synonyms_map` and _v_ the values.
    This will take a string as input, and:
    - if it is, _k_, return the string unchanged
    - if it is found in _v_, return _k_ of the corresponding list
    - else, return `None`
    """
    # Iterate over the synonyms
    for primary, synonyms in synonyms_map.items():
        # If the current config kv-pair for this field is a synonym
        if string == primary or string in synonyms:
            # Assign the "primary" key to the value
            return primary
    return None

def resolve_synonyms_in_dict(synonyms_map: Dict[str, List[str]], obj: dict) -> dict:
    resolved = {}
    for key, value in obj.items():
        resolved_key = key
        for primary, synonym in synonyms_map.items():
            if key == primary or key in synonym:
                resolved_key = primary
        if type(value) is dict:
            resolved[resolved_key] = resolve_synonyms_in_dict(synonyms_map, value)
        else:
            resolved[resolved_key] = value
    return resolved

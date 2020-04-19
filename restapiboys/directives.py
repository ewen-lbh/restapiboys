from typing import *
from restapiboys.http import RequestMethod

RESOURCE_DIRECTIVES_SYNONYMS = {
    "allowed_methods": ["allow_methods", "methods"],
    "inherits": [
        "inherit_from",
        "inherits_from",
        "inherit",
        "extends",
        "extend",
        "extends_from",
        "extend_from",
    ],
}

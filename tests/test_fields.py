from typing import *
from restapiboys import fields

def asdict(namedtuples: List[NamedTuple]) -> List[dict]:
    return [ dict(o._asdict()) for o in namedtuples ]

def test_resolve_fields_config():
    fixture = {
        'name*': {
            'one of': [4, 7, 8]
        },
        'updated_at()': {
            'is': 'datetime'
        }
    }
    expected = [
        fields.ResourceFieldConfig(
            name='name',
            whitelist=[4, 7, 8],
            type='integer',
            required=True
        ),
        fields.ResourceFieldConfig(
            name='updated_at',
            computed=True,
            type='datetime',
            read_only=True
        )
    ]
    
    actual = fields.resolve_fields_config(fixture)
    
    assert asdict(actual) == asdict(expected)

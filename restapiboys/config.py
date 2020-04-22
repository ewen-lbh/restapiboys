from restapiboys.utils import get_path, replace_whitespace_in_keys, resolve_synonyms_in_dict, yaml
from typing import *

API_CONFIG_KEYS_SYNONYMS = {
    'contact_info': ['contact_information', 'contact'],
    'verify_accounts_via': ['verify_accounts_with', 'verify_via', 'verify_with'],
    'reset_passwords_via': ['reset_passwords_with'],
    'users': ['accounts'],
    'https': ['ssl', 'http over ssl']
}

class APIConfigUsers(NamedTuple):
    fields: List[Union[Literal['email'], Literal['password'], Literal['username'], Literal['ip'], Literal['joined_at'], Literal['logged_at']]] = ['email', 'password', 'joined_at', 'logged_at', 'username']
    verify_accounts_via: Union[Literal['email'], Literal['phone'], List[Union[Literal['email'], Literal['phone']]]] = 'email'
    reset_accounts_via: Union[Literal['email'], Literal['phone'], List[Union[Literal['email'], Literal['phone']]]] = 'email'

class APIConfigContactInfo(NamedTuple):
    name: Optional[str] = None
    email: Optional[str] = None

class APIConfig(NamedTuple):
    authentification: Union[Literal['jwt'], Literal['oauth2']] = 'jwt'
    users: APIConfigUsers = APIConfigUsers()
    contact_info: APIConfigContactInfo = APIConfigContactInfo(),
    https: bool = True
    domain_name: str = 'localhost'

def get_api_config():
    filepath = get_path('config.yaml')
    parsed = yaml.load_file(filepath)
    parsed = replace_whitespace_in_keys(parsed)
    parsed = resolve_synonyms_in_dict(API_CONFIG_KEYS_SYNONYMS, parsed)
    return APIConfig(**parsed)
    

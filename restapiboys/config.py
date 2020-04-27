from restapiboys.log import debug
from restapiboys.utils import get_path, replace_whitespace_in_keys, resolve_synonyms_in_dict, yaml
from typing import *
from restapiboys import log
from enum import Enum

API_CONFIG_KEYS_SYNONYMS = {
    'contact_info': ['contact_information', 'contact'],
    'verify_accounts_via': ['verify_accounts_with', 'verify_via', 'verify_with'],
    'reset_passwords_via': ['reset_passwords_with'],
    'users': ['accounts'],
    'https': ['ssl', 'http over ssl']
}

class UsersFieldsConfig(str, Enum):
    email = 'email'
    password = 'password'
    username = 'username'
    ip_address = 'ip_address'
    joined_at = 'joined_at'
    logged_at = 'logged_at'

class AccountsContactMethod(str, Enum):
    email = 'email'
    phone = 'phone'

class AuthenticationMethod(str, Enum):
    jwt = 'jwt'
    oauth2 = 'oauth2'

class UsersConfig(NamedTuple):
    fields: List[UsersFieldsConfig] = [UsersFieldsConfig.email, UsersFieldsConfig.username, UsersFieldsConfig.password]
    verify_accounts_via: Union[AccountsContactMethod, List[AccountsContactMethod]] = AccountsContactMethod.email
    reset_passwords_via: Union[AccountsContactMethod, List[AccountsContactMethod]] = AccountsContactMethod.email

class ContactInfo(NamedTuple):
    name: Optional[str] = None
    email: Optional[str] = None

class APIConfig(NamedTuple):
    authentication: AuthenticationMethod = AuthenticationMethod.jwt
    users: UsersConfig = UsersConfig()
    contact_info: ContactInfo = ContactInfo()
    https: bool = True
    domain_name: str = 'localhost'
    documentation_url: str = 'localhost/specs'

def get_api_config():
    filepath = get_path('config.yaml')
    parsed = yaml.load_file(filepath)
    parsed = replace_whitespace_in_keys(parsed)
    parsed = resolve_synonyms_in_dict(API_CONFIG_KEYS_SYNONYMS, parsed)
    log.debug('Parsed api config (resolved synonyms): {}', parsed)
    parsed['users'] = UsersConfig(**parsed['users']) if 'users' in parsed.keys() else UsersConfig()
    parsed['contact_info'] = ContactInfo(**parsed['contact_info']) if 'contact_info' in parsed.keys() else ContactInfo()
    return APIConfig(**parsed)
    
    

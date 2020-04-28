from typing import *
from restapiboys.config import get_credentials
from restapiboys import log
import requests

COUCHDB_PORT = 5984


def create_database(name) -> bool:
    res = make_request_with_credentials('PUT', name)
    # Check if response has gone well
    return res.json().get('ok', False)

def make_request_with_credentials(
    method: str,
    url: str,
    data: Union[dict, list, None] = None,
    headers: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    headers = headers or {}
    params = params or {}
    
    base_url = f'http://127.0.0.1:{COUCHDB_PORT}'
    full_url = base_url+'/'+url
    creds = get_credentials()
    
    log.debug('Requesting CouchDB: {0} {1}', method, full_url)
    
    return requests.request(
        url=full_url,
        method=method,
        data=data,
        headers=headers,
        params=params,
        auth=(creds.username, creds.password),
    )

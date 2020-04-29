from typing import *
from uuid import UUID
from restapiboys.config import get_db_credentials
from restapiboys import log
import requests

COUCHDB_PORT = 5984


def create_database(name: str) -> bool:
    res = make_request_with_credentials("PUT", name)
    # Check if response has gone well
    return res.json().get("ok", False)

def create_item(database: str, uuid: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    res = make_request_with_credentials("PUT", f"{database}/{uuid}", data)
    return res.json()

def update_item(database: str, uuid: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    return create_item(database, uuid, data)

def read_item(database: str, uuid: UUID) -> Dict[str, Any]:
    res = make_request_with_credentials('GET', f'{database}/{uuid}')
    return res.json()

def delete_item(database: str, uuid: UUID) -> bool:
    res = make_request_with_credentials('DELETE', f'{database}/{uuid}')
    return res.json().get('ok', False)

def list_items(database: str) -> List[Dict[str, Any]]:
    res = make_request_with_credentials('GET', f'{database}/_all_docs')
    return res.json()

def delete_database(name: str) -> bool:
    res = make_request_with_credentials('DELETE', name)
    return res.json().get('ok', False)

def database_exists(name: str) -> bool:
    res = make_request_with_credentials('GET', name)
    return not res.json().get('error', None) == 'not_found'

def make_request_with_credentials(
    method: str,
    url: str,
    data: Union[dict, list, None] = None,
    headers: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    headers = headers or {}
    params = params or {}

    base_url = f"http://127.0.0.1:{COUCHDB_PORT}"
    full_url = base_url + "/" + url
    creds = get_db_credentials()

    log.debug("Requesting CouchDB: {0} {1}", method, full_url)

    return requests.request(
        url=full_url,
        method=method,
        data=data,
        headers=headers,
        params=params,
        auth=(creds.username, creds.password),
    )

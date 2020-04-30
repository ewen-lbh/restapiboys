from typing import *
from uuid import UUID
from restapiboys.config import get_db_credentials
from restapiboys import log
import requests
import json

COUCHDB_PORT = 5984

def create_database(name: str) -> bool:
    res = make_request_with_credentials("PUT", name)
    # Check if response has gone well
    return res.json().get("ok", False)


def create_item(database: str, uuid: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    res = make_request_with_credentials("PUT", f"{database}/{uuid}", data)
    ok = res.json().get('ok', False)
    if ok:
        return read_item(database, uuid)
    else:
        log.error('DB: Error while creating item: {}', res.json())
        return res.json()


def update_item(database: str, uuid: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    res = make_request_with_credentials('PUT', f"{database}/{uuid}", data, params={'rev': get_rev(database, uuid)})
    ok = res.json().get('ok', False)
    if ok:
        return read_item(database, uuid)
    else:
        log.error('DB: Error while updating item #{0}: {1}', str(uuid), res.json())
        return res.json()


def read_item(database: str, uuid: UUID) -> Dict[str, Any]:
    res = make_request_with_credentials("GET", f"{database}/{uuid}")
    return res.json()


def delete_item(database: str, uuid: UUID) -> bool:
    res = make_request_with_credentials(
        "DELETE", f"{database}/{uuid}", params={"rev": get_rev(database, uuid)}
    )
    ok = res.json().get("ok", False)
    if not ok:
        log.error("DB: Error while deleting item: {}", res.json())
    return ok


def list_items(database: str) -> List[Dict[str, Any]]:
    res = make_request_with_credentials("GET", f"{database}/_all_docs")
    rows = res.json().get("rows", [])
    items = [row["doc"] for row in rows]
    return items


def delete_database(name: str) -> bool:
    res = make_request_with_credentials("DELETE", name)
    return res.json().get("ok", False)


def database_exists(name: str) -> bool:
    dbs = make_request_with_credentials("GET", '_all_dbs').json()
    return name in dbs


def make_request_with_credentials(
    method: str,
    url: str,
    data: Union[dict, list, None] = None,
    headers: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    headers = headers or {}
    params = params or {"include_docs": True}

    base_url = f"http://127.0.0.1:{COUCHDB_PORT}"
    qs = serialize_query_string(params)
    full_url = base_url + "/" + url
    creds = get_db_credentials()

    log.debug("Requesting CouchDB:")
    log.debug("\t{0} {1}", method, full_url)
    if headers:
        log.verbatim.debug(
            "\t" + "\n\t".join([f"{k}: {v}" for k, v in headers.items()])
        )
    if data:
        log.verbatim.debug("\t" + json.dumps(data))
    if params:
        log.debug(
            "\t With params {}", qs
        )

    return requests.request(
        url=full_url,
        method=method,
        json=data,
        headers=headers,
        params=params,
        auth=(creds.username, creds.password),
    )


def get_rev(name: str, uuid: UUID) -> str:
    return read_item(name, uuid)["_rev"]

def serialize_query_string(params: Dict[str, str]) -> str:
    return "?" + "&".join([f"{k}={v}" for k, v in params.items()])

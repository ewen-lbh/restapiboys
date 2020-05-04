from restapiboys.endpoints import get_endpoints
from restapiboys.log import info, warn, error
from restapiboys.database import COUCHDB_PORT, create_database, database_exists
from typing import *
import webbrowser
import platform

def run(args: Dict[str, Any]) -> None:
    create_databases()
    url = f'http://127.0.0.1:{COUCHDB_PORT}/_utils/'
    info('Opening {} in your webbrowser...', url)
    webbrowser.open(url)

def create_databases() -> None:
    """
    Creates all missing databases, and returns a dict with the format:
    
    ```
    {
        "database_name": created? (bool),
        ...
    }
    ```
    """
    
    databases_names = [ r.identifier for r in get_endpoints() ]
    missing_databases = []

    for name in databases_names:
        if not database_exists(name):
            missing_databases.append(name)
    
    if missing_databases:
        warn('Missing {} databases', len(missing_databases))
        for db_name in missing_databases:
            info('\t- Creating database {}', db_name)
            created = create_database(db_name)
            if not created:
                error('\t  Could not create {}', db_name)
            
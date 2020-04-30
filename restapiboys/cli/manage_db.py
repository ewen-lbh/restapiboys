from restapiboys.endpoints import get_endpoints
from restapiboys.log import info
from restapiboys.database import COUCHDB_PORT, create_database, database_exists
from typing import *
import webbrowser
import platform

def run(args: Dict[str, Any]) -> None:
    create_databases()
    url = f'http://127.0.0.1:{COUCHDB_PORT}/_utils/'
    info('Opening {} in your webbrowser...', url)
    webbrowser.open(url)

def create_databases() -> Dict[str, bool]:
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
    created_databases = {}

    for name in databases_names:
        if not database_exists(name):
            info('Database {} does not exist, creating it...', name)
            created = create_database(name)
            created_databases[name] = created

    return created_databases
            

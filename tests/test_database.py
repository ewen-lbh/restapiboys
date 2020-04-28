from restapiboys import database

def test_create_database():
    assert database.create_database('john')
    # Cleanup
    database.make_request_with_credentials('DELETE', 'john')
    

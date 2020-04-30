from uuid import uuid4
from restapiboys import database

def test_create_delete_database():
    assert database.create_database('john')
    assert database.delete_database('john')

class Test:
    def setup_method(self, test_method):
        database.create_database('john')
    
    def teardown_method(self, test_method):
        database.delete_database('john')

    def test_insert_list_item(self):
        uuid = uuid4()
        database.create_item('john', uuid, dict(lorem='ipsum'))
        
        items = database.list_items('john')
        assert items[0]['lorem'] == 'ipsum'
        assert items[0]['_id'] == str(uuid)

    def test_get_item(self):
        uuid = uuid4()
        database.create_item('john', uuid, dict(lorem='ipsum'))
        
        item = database.read_item('john', uuid)
        assert item['lorem'] == 'ipsum'
        assert item['_id'] == str(uuid)

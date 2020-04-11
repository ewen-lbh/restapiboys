from restapiboys import HTTP

@HTTP.GET('/courses/:start/:end')
def response(db, req, start: str, end: str):
  events = db.get('events').of_user(req)
  if not events.count():
    return HTTP.EMTPY
  
  
from restapiboys.http import Request, Response, StatusCode
from restapiboys.custom_routes.decorators import GET
from restapiboys.database import list_items

@GET('/courses/:start/:end')
def response(req: Request, start: str, end: str) -> Response:
  events = list_items('events')
  if not len(events):
    return Response(StatusCode.NO_CONTENT)
    
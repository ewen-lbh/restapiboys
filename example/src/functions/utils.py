import datetime
import slugify
import re

# TODO: use a library instead
# @ http://www.urlregex.com/
URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

def now() -> str:
  return datetime.datetime.now().isoformat()

def is_url(maybe_url) -> bool:
  return URL_PATTERN.match(maybe_url) is not None

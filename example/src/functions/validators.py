import re

PATTERN_CSS_HEX_COLOR = re.compile(r'#[0-9a-fA-F]{3}[0-9a-fA-F]{3}?')

def is_valid_hex_color(value: str) -> bool:
  return PATTERN_CSS_HEX_COLOR.match(value) is not None

from termcolor import colored

def get_logger_func(normal_style, variable_style, icon=''):
  variable_color = variable_style.get('color', 'white')
  normal_color = normal_style.get('color', 'white')
  if 'color' in variable_style.keys(): del variable_style['color']
  if 'color' in normal_style.keys(): del normal_style['color']
  
  def func(content, **variables):
    variables = { k:colored(v, variable_color, **variable_style) for k, v in variables.items() }
    content = colored(content, normal_color, **normal_style)
    print(str(icon)+(' ' if icon else '')+content.format(**variables))
  return func

class Logger:
  def __init__(self, args) -> None:
    self.verbose_lv = 3
    if args['--quiet']: self.verbose_lv = 0 
    if args['--verbose']: self.verbose_lv = args['--verbose']  + 1
  
  def debug(self, message, **variables):
    if self.verbose_lv >= 4:
      get_logger_func(
        normal_style={ 'attrs': ['dark'] },
        variable_style={ 'attrs': ['bold'] },
      )(message, **variables)
    
  def info(self, message, **variables):
    if self.verbose_lv >= 3:
      get_logger_func(
        normal_style={},
        variable_style={ 'color': 'cyan', 'attrs': ['bold'] },
        icon=colored('ℹ', 'cyan')
      )(message, **variables)

  def warn(self, message, **variables):
    if self.verbose_lv >= 2:
      get_logger_func(
        normal_style={ 'color': 'yellow' },
        variable_style={ 'color': 'white', 'attrs': ['bold'] },
        icon=colored('⚠', 'yellow')
      )(message, **variables)
  
  def error(self, message, **variables):
    if self.verbose_lv >= 1:
      get_logger_func(
        normal_style={ 'color': 'red' },
        variable_style={ 'color': 'white', 'attrs': ['bold'] },
        icon=colored('×', 'red')
      )(message, **variables)

  def success(self, message, **variables):
    if self.verbose_lv >= 3:
      get_logger_func(
        normal_style={ 'color': 'green' },
        variable_style={ 'color': 'white', 'attrs': ['bold'] },
        icon=colored('√', 'green')
      )(message, **variables)

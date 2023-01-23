from django.core.exceptions import ValidationError

class ComplianceError(Exception):
  def __init__(self, current, expected):
    super().__init__(f'Compliance Error: Expected version is {expected} (recieved {current})')

def comply(version):
  def _comply(func):
    def _func(*args, __v=None, **kwargs):
      if __v != version:
        raise ComplianceError(__v, version)
      return func(*args, **kwargs)
    return _func
  return _comply

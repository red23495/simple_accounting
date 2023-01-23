import unittest

class ComplianceTest(unittest.TestCase):

  def test_compliance_decorator(self):
    from .utils import comply, ComplianceError
    @comply(1)
    def a(x,y,*,z=1):
      return x + y + z
    try:
      self.assertEqual(a(1, 2, z=3, __v=1), 6)
    except ComplianceError:
      self.fail('Compliance raised error even when compliance is met')
    self.assertRaises(ComplianceError, a, __v=2)

from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Account

class AccountModelTest(TestCase):

  sample_asset = {
    "name": "Cash",
    "account_number": "1",
    "account_type": Account.AccountTypes.ASSET,
    "parent": None,
    "description": "all cash",
    "inactive": False,
  }

  sample_liability = {
    "name": "Account Payable",
    "account_number": "2",
    "account_type": Account.AccountTypes.LIABILITY,
    "parent": None,
    "description": "all amounts payable",
    "inactive": False,
  }

  def test_accounts_are_created_properly(self):
      asset = Account(**self.sample_asset)
      asset.full_clean()
      asset.save()
      self.assertEqual(asset.name, 'Cash')
      self.assertEqual(asset.account_number, '1')
      self.assertEqual(asset.account_type, Account.AccountTypes.ASSET)
      self.assertEqual(asset.parent, None)
      self.assertEqual(asset.description, "all cash")
      self.assertEqual(asset.inactive, False)

  def test_name_cant_be_empty(self):
    """Account name can't be empty"""
    self.assertRaises(ValidationError, lambda kwargs: Account(**kwargs).full_clean(), {**self.sample_liability, 'name': '    '})

  def test_number_cant_be_empty(self):
    """Account number can't be empty"""
    self.assertRaises(ValidationError, lambda kwargs: Account(**kwargs).full_clean(), {**self.sample_liability, 'account_number': '    '})

  def test_number_must_be_unique(self):
    """Account number must be unique"""
    Account(**self.sample_asset).save()
    self.assertRaises(ValidationError, lambda kwargs: Account(**kwargs).full_clean(), {
      **self.sample_liability, 'account_number': self.sample_asset['account_number']
    })
    
  def test_sub_account_number_must_have_parent_number_as_prefix(self):
    """Sub Account number should have parent account number as prefix"""
    parent = Account(**self.sample_asset)
    parent.save()
    sub_account_1 = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "some cash",
      "inactive": False,
    }
    sub_account_2 = {
      "name": "Cash 2",
      "account_number": "2.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "other cash",
      "inactive": False,
    }
    try:
      Account(**sub_account_1).full_clean()
    except:
      self.fail("Couldn't create account with correct prefix")
    self.assertRaises(ValidationError, lambda kwargs: Account(**kwargs).full_clean(), sub_account_2)

  def test_sub_account_must_have_same_type_as_parent_account(self):
    """sub accounts must have same type as parent account"""
    parent = Account(**self.sample_asset)
    parent.save()
    sub_account_1 = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "some cash",
      "inactive": False,
    }
    sub_account_2 = {
      "name": "Cash 2",
      "account_number": "1.2",
      "account_type": Account.AccountTypes.LIABILITY,
      "parent": parent,
      "description": "other cash",
      "inactive": False,
    }
    try:
      Account(**sub_account_1).full_clean()
    except:
      self.fail("Couldn't create account with correct type")
    self.assertRaises(ValidationError, lambda kwargs: Account(**kwargs).full_clean(), sub_account_2)

  def account_can_have_any_number_of_sub_account(self):
    """Account can have any number of sub account"""
    parent = Account(**self.sample_asset)
    parent.save()
    sub_account_1 = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "some cash",
      "inactive": False,
    }
    sub_account_2 = {
      "name": "Cash 2",
      "account_number": "1.2",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "other cash",
      "inactive": False,
    }
    sub_account_3 = {
      "name": "Cash 3",
      "account_number": "1.3",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "leftover cash",
      "inactive": False,
    }
    try:
      a1 = Account(**sub_account_1).full_clean()
      a2 = Account(**sub_account_2).full_clean()
      a3 = Account(**sub_account_3).full_clean()
      a1.save()
      a2.save()
      a3.save()
    except:
      self.fail("Couldn't create account with correct info")

  def sub_account_can_any_number_of_sub_account(self):
    """Sub Account can have any number of sub account"""
    """Account can have any number of sub account"""
    parent = Account(**self.sample_asset)
    parent.save()
    sub_account = {
      "name": "Cash A",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "some cash",
      "inactive": False,
    }
    sub = Account(**sub_account).save()
    sub_account_1 = {
      "name": "Cash 1",
      "account_number": "1.1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": sub,
      "description": "some cash",
      "inactive": False,
    }
    sub_account_2 = {
      "name": "Cash 2",
      "account_number": "1.1.2",
      "account_type": Account.AccountTypes.ASSET,
      "parent": sub,
      "description": "other cash",
      "inactive": False,
    }
    sub_account_3 = {
      "name": "Cash 3",
      "account_number": "1.1.3",
      "account_type": Account.AccountTypes.ASSET,
      "parent": sub,
      "description": "leftover cash",
      "inactive": False,
    }
    try:
      a1 = Account(**sub_account_1).full_clean()
      a2 = Account(**sub_account_2).full_clean()
      a3 = Account(**sub_account_3).full_clean()
      a1.save()
      a2.save()
      a3.save()
    except:
      self.fail("Couldn't create account with correct info")

  def test_account_type_cant_be_empty(self):
    """Account type cant be empty"""
    self.assertRaises(ValidationError, lambda kwargs: Account(**kwargs).full_clean(), {**self.sample_liability, 'account_type': None})

  def test_setting_account_inactive_makes_all_sub_accounts_inactive(self):
    """Setting an account inactive makes all subaccounts inactive"""
    parent = Account(**self.sample_asset)
    parent.save()
    sub_account_1 = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "some cash",
      "inactive": False,
    }
    sub_account_2 = {
      "name": "Cash 2",
      "account_number": "1.2",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "other cash",
      "inactive": False,
    }
    sub_account_3 = {
      "name": "Cash 3",
      "account_number": "1.3",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "leftover cash",
      "inactive": False,
    }
    s1 = Account(**sub_account_1)
    s2 = Account(**sub_account_2)
    s3 = Account(**sub_account_3)
    s1.save()
    s2.save()
    s3.save()
    parent.inactive = True
    parent.save()
    s1.refresh_from_db()
    s2.refresh_from_db()
    s3.refresh_from_db()
    self.assertEqual(s1.inactive, True)
    self.assertEqual(s2.inactive, True)
    self.assertEqual(s3.inactive, True)

  def test_str_representation(self):
    """Account shows it's representation in str properly"""
    self.assertEqual(str(Account(**self.sample_asset)), "1 - Cash")

  def test_inactive_parent_cant_create_subchild(self):
    """Inactive parent can't create sub account"""
    parent = Account(**{**self.sample_asset, 'inactive': True})
    parent.save()
    sub_account = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "some cash",
      "inactive": False,
    }
    self.assertRaises(ValidationError, lambda kwargs: Account(**kwargs).full_clean(), sub_account)

  def test_inactive_child_can_be_edited(self):
    """Inactive parent can't create sub account"""
    parent = Account(**self.sample_asset)
    parent.save()
    sub_account = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "some cash",
      "inactive": False,
    }
    child = Account(**sub_account)
    child.save()
    parent.inactive = True
    parent.save()
    child.name = 'CASH 1'
    try:
      child.save()
    except:
      self.fail('could not edit sub account when account is inactive')

  def test_cant_make_subaccount_active_if_parent_inactive(self):
    """Can't make sub account active if parent account is inactive"""
    parent = Account(**self.sample_asset)
    parent.full_clean()
    parent.save()
    sub_account_1 = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent,
      "description": "some cash",
      "inactive": False,
    }
    sub = Account(**sub_account_1)
    sub.full_clean()
    sub.save()
    parent.inactive = True
    parent.save()
    sub.refresh_from_db()
    self.assertEqual(sub.inactive, True)
    sub.inactive = False
    self.assertRaises(ValidationError, sub.full_clean)

from django.test import TestCase
from .models import Account, VoucherType, Voucher, Ledger
from .forms import AccountForm, VoucherTypeForm, VoucherForm, LedgerForm, LedgerInlineFormset
import datetime

class AccountFormTest(TestCase):

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

  def test_validates_correct_data(self):
    "validates correct data"
    asset = AccountForm(self.sample_asset)
    liability = AccountForm(self.sample_liability)
    self.assertTrue(asset.is_valid())
    self.assertTrue(liability.is_valid())

  def test_name_cant_be_empty(self):
    """Account name can't be empty"""
    self.assertFalse(AccountForm({**self.sample_liability, 'name': '    '}).is_valid())

  def test_number_cant_be_empty(self):
    """Account number can't be empty"""
    self.assertFalse(AccountForm({**self.sample_liability, 'account_number': '    '}).is_valid())

  def test_number_must_be_unique(self):
    """Account number must be unique"""
    Account(**self.sample_asset).save()
    self.assertFalse(AccountForm({**self.sample_liability, 'account_number': self.sample_asset['account_number']}).is_valid())
    
  def test_sub_account_number_must_have_parent_number_as_prefix(self):
    """Sub Account number should have parent account number as prefix"""
    parent = Account(**self.sample_asset)
    parent.save()
    sub_account_1 = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent.pk,
      "description": "some cash",
      "inactive": False,
    }
    sub_account_2 = {
      "name": "Cash 2",
      "account_number": "2.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent.pk,
      "description": "other cash",
      "inactive": False,
    }
    self.assertTrue(AccountForm(sub_account_1).is_valid())
    self.assertFalse(AccountForm(sub_account_2).is_valid())

  def test_sub_account_must_have_same_type_as_parent_account(self):
    """sub accounts must have same type as parent account"""
    parent = Account(**self.sample_asset)
    parent.save()
    sub_account_1 = {
      "name": "Cash 1",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
      "parent": parent.pk,
      "description": "some cash",
      "inactive": False,
    }
    sub_account_2 = {
      "name": "Cash 2",
      "account_number": "1.2",
      "account_type": Account.AccountTypes.LIABILITY,
      "parent": parent.pk,
      "description": "other cash",
      "inactive": False,
    }
    self.assertTrue(AccountForm(sub_account_1).is_valid())
    self.assertFalse(AccountForm(sub_account_2).is_valid())

  def test_account_type_cant_be_empty(self):
    """Account type cant be empty"""
    self.assertFalse(AccountForm({**self.sample_liability, 'account_type': None}).is_valid())

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
    self.assertFalse(AccountForm(sub_account).is_valid())

  def test_inactive_child_can_be_edited(self):
    """Inactive child can be edited"""
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
    child.refresh_from_db()
    child_form = AccountForm({**sub_account, 'inactive': True, 'name': 'Cash 1'}, instance=child)
    self.assertTrue(child_form.is_valid())

  def test_cant_make_subaccount_active_if_parent_inactive(self):
    """Can't make sub account active if parent account is inactive"""
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
    sub = Account(**sub_account_1)
    sub.save()
    parent.inactive = True
    parent.save()
    sub.refresh_from_db()
    self.assertEqual(sub.inactive, True)
    child_form = AccountForm({**sub_account_1, 'inactive': False}, instance=sub)
    self.assertFalse(child_form.is_valid())

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

class VoucherTypeFormTest(TestCase):

  sale_voucher = {
    "name": "Sale Voucher",
    "prefix": "SV"
  }

  purchase_voucher = {
    "name": "Purchase Voucher",
    "prefix": "PV"
  }

  def test_validates_correct_data(self):
    """validates correct data"""
    sale = VoucherTypeForm(self.sale_voucher)
    purchase = VoucherTypeForm(self.purchase_voucher)
    self.assertTrue(sale.is_valid())
    self.assertTrue(purchase.is_valid())

  def test_name_must_be_non_empty(self):
    """name can't be empty"""
    sale = VoucherTypeForm({**self.sale_voucher, 'name': '       '})
    self.assertFalse(sale.is_valid())

  def test_prefix_must_be_non_empty(self):
    """prefix can't be empty"""
    sale = VoucherTypeForm({**self.sale_voucher, 'prefix': '       '})
    self.assertFalse(sale.is_valid())

  def test_prefix_must_be_unique(self):
    """prefix must be unique"""
    sale = VoucherTypeForm(self.sale_voucher).save()
    purchase = VoucherTypeForm({**self.purchase_voucher, 'prefix': self.sale_voucher['prefix']})
    self.assertFalse(purchase.is_valid())

class VoucherTypeModelTest(TestCase):

  sale_voucher = {
    "name": "Sale Voucher",
    "prefix": "SV"
  }

  purchase_voucher = {
    "name": "Purchase Voucher",
    "prefix": "PV"
  }

  def test_types_are_created_properly(self):
    """Voucher types can be created properly"""
    try:
      sale = VoucherType(**self.sale_voucher)
      purchase = VoucherType(**self.purchase_voucher)
      sale.full_clean()
      purchase.full_clean()
      sale.save()
      purchase.save()
    except:
      self.fail('Could not create voucher types')
    self.assertEqual(sale.name, "Sale Voucher")
    self.assertEqual(sale.prefix, "SV")
    self.assertEqual(purchase.name, "Purchase Voucher")
    self.assertEqual(purchase.prefix, "PV")

  def test_type_can_generate_unique_sequence(self):
    """types can generate unique sequence"""
    sale = VoucherType(**self.sale_voucher)
    self.assertEqual(sale.generate_number(), 'SV-0001')
    self.assertEqual(sale.generate_number(), 'SV-0002')

  def test_generated_sequences_are_independent(self):
    """generated sequences are independent"""
    sale = VoucherType(**self.sale_voucher)
    self.assertEqual(sale.generate_number(), 'SV-0001')
    purchase = VoucherType(**self.purchase_voucher)
    self.assertEqual(purchase.generate_number(), 'PV-0001')

  def test_str_representation(self):
    """converts to string properly"""
    sale = VoucherType(**self.sale_voucher)
    self.assertEqual(str(sale), 'Sale Voucher (SV)')

class VoucherFormTest(TestCase):

  def setUp(self):
    self.vtype = VoucherType(**{
      "name": "Sale Voucher",
      "prefix": "SV"
    })
    self.vtype.save()
    self.voucher_data = {
      "voucher_date": "2022-01-01",
      "voucher_type": self.vtype,
      "description": "This voucher happened",
      "status": Voucher.Status.PENDING,
    }

  def test_validates_correct_data(self):
    """validates correct data"""
    voucher = VoucherForm(self.voucher_data)
    self.assertTrue(voucher.is_valid())

  def test_date_cant_be_empty(self):
    """Date can't be empty"""
    voucher = VoucherForm({**self.voucher_data, 'voucher_date': None})
    self.assertFalse(voucher.is_valid())

  def test_type_cant_be_empty(self):
    """Type cant be empty"""
    voucher = VoucherForm({**self.voucher_data, 'voucher_type': None})
    self.assertFalse(voucher.is_valid())

class LedgerFormTest(TestCase):

  def setUp(self):
    self.cash = Account(**{
      "name": "Cash",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
    })
    self.cash.save()
    self.vtype = VoucherType(**{
      "name": "Sale Voucher",
      "prefix": "SV"
    })
    self.vtype.save()
    self.voucher = Voucher(**{
      "voucher_date": "2022-01-01",
      "voucher_type": self.vtype,
      "description": "This voucher happened",
      "status": Voucher.Status.PENDING,
    })
    self.voucher.save()
    self.voucher.refresh_from_db()
    self.ledger_data = {
      "voucher": self.voucher,
      "account": self.cash,
      "amount": 100,
    }

  def test_validates_correct_data(self):
    """validates correct data"""
    ledger = LedgerForm(self.ledger_data)
    self.assertTrue(ledger.is_valid())

  def test_ledger_account_cant_be_empty(self):
    """Ledger Account can't be empty"""
    ledger = LedgerForm({**self.ledger_data, 'account': None})
    self.assertFalse(ledger.is_valid())

  def test_ledger_amount_cant_be_zero(self):
    """Amount can't be zero"""
    ledger = LedgerForm({**self.ledger_data, 'amount': 0})
    self.assertFalse(ledger.is_valid())

class LedgerModelTest(TestCase):

  def setUp(self):
    self.cash = Account(**{
      "name": "Cash",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
    })
    self.cash.save()
    self.vtype = VoucherType(**{
      "name": "Sale Voucher",
      "prefix": "SV"
    })
    self.vtype.save()
    self.voucher = Voucher(**{
      "voucher_date": "2022-01-01",
      "voucher_type": self.vtype,
      "description": "This voucher happened",
      "status": Voucher.Status.PENDING,
    })
    self.voucher.save()
    self.voucher.refresh_from_db()
    self.ledger_data = {
      "voucher": self.voucher,
      "account": self.cash,
      "amount": 100,
    }

  def test_vouchers_are_created_properly(self):
    """ledgers are created properly"""
    ledger = Ledger(**self.ledger_data)
    ledger.save()
    ledger.refresh_from_db()
    self.assertEqual(ledger.voucher.pk, self.voucher.pk)
    self.assertEqual(ledger.account.pk, self.cash.pk)
    self.assertEqual(ledger.amount, 100)
  
  def test_str_representation(self):
    """converts to string properly"""
    ledger = Ledger(**self.ledger_data)
    ledger.save()
    self.assertEqual(str(ledger), f'{ledger.voucher.voucher_number} - {ledger.account.name}')

class LedgerInlineFormsetTest(TestCase):

  def setUp(self):
    self.cash = Account(**{
      "name": "Cash",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
    })
    self.bank = Account(**{
      "name": "Bank",
      "account_number": "1.2",
      "account_type": Account.AccountTypes.ASSET,
    })
    self.equity = Account(**{
      "name": "Equity",
      "account_number": "2.1",
      "account_type": Account.AccountTypes.EQUITY,
    })
    self.revenue = Account(**{
      "name": "Revenue",
      "account_number": "3.1",
      "account_type": Account.AccountTypes.REVENUE,
    })
    self.cash.save()
    self.bank.save()
    self.revenue.save()
    self.equity.save()
    self.vtype = VoucherType(**{
      "name": "Sale Voucher",
      "prefix": "SV"
    })
    self.vtype.save()
    self.voucher = Voucher(**{
      "voucher_date": "2022-01-01",
      "voucher_type": self.vtype,
      "description": "This voucher happened",
      "status": Voucher.Status.PENDING,
    })
    self.voucher.save()
    self.voucher.refresh_from_db()
    self.ledgers = [
      {
        "account": self.cash.pk,
        "amount": 100,
      },
      {
        "account": self.bank.pk,
        "amount": 200,
      },
      {
        "account": self.equity.pk,
        "amount": 120,
      },
      {
        "account": self.revenue.pk,
        "amount": 180,
      }
    ]

  def prepare_form_data(self, data, prefix='form'):
    out = {}
    out[f'{prefix}-TOTAL_FORMS'] = '4'
    out[f'{prefix}-INITIAL_FORMS'] = '0'
    for i in range(len(data)):
      for k, v in data[i].items():
        out[f'{prefix}-{i}-{k}'] = v
    return out
      

  def test_debit_and_credit_must_be_equal(self):
    """Debit and credit must be equal"""
    formset = LedgerInlineFormset(self.prepare_form_data(self.ledgers, 'ledgers'))
    self.assertTrue(formset.is_valid())
    ledgers = [{**ledger} for ledger in self.ledgers]
    ledgers[0]['amount'] = 1000
    formset = LedgerInlineFormset(self.prepare_form_data(ledgers, 'ledgers'))
    self.assertFalse(formset.is_valid())

class VoucherAndLedgerModelTest(TestCase):

  def setUp(self):
    self.cash = Account(**{
      "name": "Cash",
      "account_number": "1.1",
      "account_type": Account.AccountTypes.ASSET,
    })
    self.bank = Account(**{
      "name": "Bank",
      "account_number": "1.2",
      "account_type": Account.AccountTypes.ASSET,
    })
    self.equity = Account(**{
      "name": "Equity",
      "account_number": "2.1",
      "account_type": Account.AccountTypes.EQUITY,
    })
    self.revenue = Account(**{
      "name": "Revenue",
      "account_number": "3.1",
      "account_type": Account.AccountTypes.REVENUE,
    })
    self.cash.save()
    self.bank.save()
    self.revenue.save()
    self.equity.save()
    self.vtype = VoucherType(**{
      "name": "Sale Voucher",
      "prefix": "SV"
    })
    self.vtype.save()
    self.voucher_data = {
      "voucher_date": "2022-01-01",
      "voucher_type": self.vtype,
      "description": "This voucher happened",
      "status": Voucher.Status.PENDING,
    }
    self.ledgers = [
      {
        "account": self.cash,
        "amount": 100,
      },
      {
        "account": self.bank,
        "amount": 200,
      },
      {
        "account": self.equity,
        "amount": 120,
      },
      {
        "account": self.revenue,
        "amount": 180,
      }
    ]

  def test_vouchers_are_created_properly(self):
    """Vouchers are created properly"""
    voucher = Voucher(**self.voucher_data)
    voucher.save()
    voucher.refresh_from_db()
    self.assertEqual(voucher.voucher_number, 'SV-0001')
    self.assertEqual(voucher.voucher_date, datetime.date(2022, 1, 1))
    self.assertEqual(voucher.voucher_type.prefix, self.vtype.prefix)
    self.assertEqual(voucher.description, "This voucher happened")
    self.assertEqual(voucher.status, Voucher.Status.PENDING)

  def test_number_is_autogenerated(self):
    """Voucher number is auto generated"""
    voucher = Voucher(**self.voucher_data)
    voucher.save()
    self.assertEqual(voucher.voucher_number, "SV-0001")

  def test_shows_proper_amount(self):
    """Shows proper amount"""
    voucher = Voucher(**self.voucher_data)
    voucher.save()
    for ledger in self.ledgers:
      Ledger(**ledger, voucher=voucher).save()
    self.assertEqual(voucher.amount, 300)

  def test_sorts_debits_and_credits_properly(self):
    """sorts debit credits properly"""
    voucher = Voucher(**self.voucher_data)
    voucher.save()
    for ledger in self.ledgers:
      Ledger(**ledger, voucher=voucher).save()
    for ledger in voucher.debits:
      self.assertIn(ledger.account.account_type, (Account.AccountTypes.ASSET, Account.AccountTypes.EXPENSE))
    for ledger in voucher.credits:
      self.assertIn(ledger.account.account_type, (Account.AccountTypes.EQUITY, Account.AccountTypes.LIABILITY, Account.AccountTypes.REVENUE))
    for ledger in voucher.ledgers.all():
      ledger.amount *= -1
      ledger.save()
    for ledger in voucher.credits:
      self.assertIn(ledger.account.account_type, (Account.AccountTypes.ASSET, Account.AccountTypes.EXPENSE))
    for ledger in voucher.debits:
      self.assertIn(ledger.account.account_type, (Account.AccountTypes.EQUITY, Account.AccountTypes.LIABILITY, Account.AccountTypes.REVENUE))
    
  def test_voucher_str_representation(self):
    """voucher converts to string properly"""
    voucher = Voucher(**self.voucher_data)
    voucher.save()
    self.assertEqual(str(voucher), voucher.voucher_number)

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

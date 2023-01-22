from django.db import models
from datetime import datetime, date
from django.db import transaction
from django.core.exceptions import ValidationError
from sequences import get_next_value
from decimal import Decimal
from .utils import comply

def non_empty_validator(value: str):
  if len(value.strip()) == 0:
      raise ValidationError('This field can not be empty')

def non_zero_validator(value):
  if value == 0:
    raise ValidationError('This field can not be 0')

class AccountQuerySet(models.QuerySet):

  version = 1

  @comply(version)
  def create(self, **kwargs):
    return super().create(**kwargs)

  @comply(version)
  def update(self, **kwargs) -> int:
    return super().update(**kwargs)

class Account(models.Model):

  objects = AccountQuerySet.as_manager()

  class AccountTypes(models.IntegerChoices):
    ASSET = 1
    LIABILITY = 2
    EQUITY = 3
    REVENUE = 4
    EXPENSE = 5

  name: str = models.CharField(max_length=256, blank=False)
  account_number: str = models.CharField(max_length=32, unique=True, blank=False, db_index=True)
  account_type: AccountTypes = models.IntegerField(choices=AccountTypes.choices, null=False, blank=False)
  parent: "Account" = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
  description: str = models.TextField(blank=True)
  created_at: datetime = models.DateTimeField(auto_now_add=True)
  updated_at: datetime = models.DateTimeField(auto_now=True)
  inactive: bool = models.BooleanField(default=False)

  _inactive_changed = False

  def __setattr__(self, __name: str, __value: any):
    if hasattr(self, '_state') and self._state.adding == False and __name == 'inactive' and __value != self.inactive:
      self._inactive_changed = True
    return super().__setattr__(__name, __value)

  def save(self, **kwargs):
    with transaction.atomic():
      super(Account, self).save(**kwargs)
      if self._inactive_changed:
        Account.objects.filter(account_number__startswith=self.account_number).update(inactive=self.inactive, __v=1)
        self._inactive_changed = False

  def __str__(self):
    return f"{self.account_number} - {self.name}"


class VoucherType(models.Model):
  
  name: str = models.CharField(max_length=128, blank=False, validators=[non_empty_validator])
  prefix: str = models.CharField(max_length=4, unique=True, blank=False, validators=[non_empty_validator])

  def generate_number(self):
    return f'{self.prefix}-{str(get_next_value(self.prefix)).zfill(4)}'

  def __str__(self):
    return f'{self.name} ({self.prefix})'

class Voucher(models.Model):

  class Status(models.IntegerChoices):
    PENDING = 1
    APPROVED = 2
    REJECTED = 3

  voucher_number: str = models.CharField(max_length=12, editable=False)
  voucher_date: date = models.DateField()
  voucher_type: VoucherType = models.ForeignKey(VoucherType, on_delete=models.CASCADE, blank=False, null=False)
  description: str = models.TextField(null=True, blank=True)
  status: Status = models.IntegerField(choices=Status.choices, blank=False, default=Status.PENDING)
  created_at: datetime = models.DateTimeField(auto_now_add=True)
  updated_at: datetime = models.DateTimeField(auto_now=True)

  _status_changed = False

  def __setattr__(self, __name: str, __value: any) -> None:
    if hasattr(self, '_state') and not self._state.adding and __name == 'status' and __value != self.status:
      self._status_changed = True
    return super().__setattr__(__name, __value)

  def set_ledgers(self, ledgers):
    with transaction.atomic():
      for ledger in ledgers:
        if isinstance(ledger, dict):
          ledger = Ledger(**ledger)
        ledger.voucher = self
        ledger.status = self.status
        ledger.full_clean()
        ledger.save()
      debit_amount = sum(item.amount for item in self.debits)
      credit_amount = sum(item.amount for item in self.credits)
      if debit_amount != credit_amount:
        raise ValidationError('Debit Credit must be equal')

  @property
  def debits(self):
    ledgers = self.ledgers.all()
    debits = []
    for ledger in ledgers:
      if ledger.amount > 0 and ledger.account.account_type in [Account.AccountTypes.ASSET, Account.AccountTypes.EXPENSE]:
        debits.append(ledger)
      elif ledger.amount < 0 and ledger.account.account_type in [Account.AccountTypes.LIABILITY, Account.AccountTypes.EQUITY, Account.AccountTypes.REVENUE]:
        debits.append(ledger)
    return debits

  @property
  def credits(self):
    ledgers = self.ledgers.all()
    credits = []
    for ledger in ledgers:
      if ledger.amount < 0 and ledger.account.account_type in [Account.AccountTypes.ASSET, Account.AccountTypes.EXPENSE]:
        credits.append(ledger)
      elif ledger.amount > 0 and ledger.account.account_type in [Account.AccountTypes.LIABILITY, Account.AccountTypes.EQUITY, Account.AccountTypes.REVENUE]:
        credits.append(ledger)
    return credits

  @property
  def amount(self):
    return sum(item.amount for item in self.debits)

  def save(self, **kwargs):
    with transaction.atomic():
      if self._state.adding:
        self.voucher_number = self.voucher_type.generate_number()
      super(Voucher, self).save(**kwargs)
      if self._status_changed:
        Ledger.objects.filter(voucher=self).update(status=self.status)
        self._status_changed = False

  def __str__(self):
    return self.voucher_number

class Ledger(models.Model):

  voucher: Voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, null=False, blank=False, related_name='ledgers')
  account: Account = models.ForeignKey(Account, on_delete=models.CASCADE, null=False, blank=False, related_name='+')
  amount: Decimal = models.DecimalField(max_digits=30, decimal_places=6, validators=[non_zero_validator])
  status: Voucher.Status = models.IntegerField(choices=Voucher.Status.choices)
  created_at: datetime = models.DateTimeField(auto_now_add=True)
  updated_at: datetime = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.voucher.voucher_number} - {self.account.name}'
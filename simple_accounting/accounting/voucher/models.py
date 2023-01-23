from django.db import models
from datetime import datetime, date
from django.db import transaction
from sequences import get_next_value
from accounting.utils import comply
from accounting.account.models import Account
from decimal import Decimal

class VoucherType(models.Model):
  
  name: str = models.CharField(max_length=128, blank=False)
  prefix: str = models.CharField(max_length=4, unique=True, blank=False)

  def generate_number(self):
    return f'{self.prefix}-{str(get_next_value(self.prefix)).zfill(4)}'

  def __str__(self):
    return f'{self.name} ({self.prefix})'

class VoucherQuerySet(models.QuerySet):

  version = 1
  # 1 - autogenerates number from type when created, number is not editable

  @comply(version)
  def create(self, **kwargs):
    return super().create(**kwargs)

  @comply(version)
  def update(self, **kwargs) -> int:
    return super().update(**kwargs)

class Voucher(models.Model):

  class Status(models.IntegerChoices):
    PENDING = 1
    APPROVED = 2
    REJECTED = 3

  voucher_number: str = models.CharField(max_length=12, editable=False)
  voucher_date: date = models.DateField()
  voucher_type: VoucherType = models.ForeignKey(VoucherType, on_delete=models.CASCADE, blank=False, null=False)
  description: str = models.TextField(null=True, blank=True)
  status: int = models.IntegerField(choices=Status.choices, blank=False, default=Status.PENDING)
  created_at: datetime = models.DateTimeField(auto_now_add=True)
  updated_at: datetime = models.DateTimeField(auto_now=True)

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

  def __str__(self):
    return self.voucher_number

class Ledger(models.Model):

  voucher: Voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, null=False, blank=False, related_name='ledgers')
  account: Account = models.ForeignKey(Account, on_delete=models.CASCADE, null=False, blank=False, related_name='+')
  amount: Decimal = models.DecimalField(max_digits=30, decimal_places=6)
  created_at: datetime = models.DateTimeField(auto_now_add=True)
  updated_at: datetime = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'{self.voucher.voucher_number} - {self.account.name}'
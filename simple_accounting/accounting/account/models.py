from django.db import models
from datetime import datetime
from django.db import transaction
from accounting.utils import comply

class AccountQuerySet(models.QuerySet):

  version = 1
  # 1 - parent accounts active status is propagated to all sub accounts

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
  account_type: int = models.IntegerField(choices=AccountTypes.choices, null=False, blank=False)
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

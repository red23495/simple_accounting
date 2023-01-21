from django.db import models
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError

class Account(models.Model):

  class AccountTypes(models.IntegerChoices):
    ASSET = 1
    LIABILITY = 2
    EQUITY = 3
    REVENUE = 4
    EXPENSE = 5

  name: str = models.CharField(max_length=256, blank=False)
  account_number: str = models.CharField(max_length=32, unique=True, blank=False, db_index=True)
  account_type: AccountTypes = models.IntegerField(choices=AccountTypes.choices)
  parent: "Account" = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
  description: str = models.TextField(blank=True)
  created_at: datetime = models.DateTimeField(auto_now_add=True)
  updated_at: datetime = models.DateTimeField(auto_now=True)
  inactive: bool = models.BooleanField(default=False)

  _inactive_changed = False

  def __setattr__(self, __name: str, __value: any) -> None:
    if hasattr(self, '_state') and self._state.adding == False and __name == 'inactive' and __value != self.inactive:
      self._inactive_changed = True
    return super().__setattr__(__name, __value)

  def clean(self):
    errors = {}
    if not len(self.name.strip()) > 0:
      errors['name'] = "name can not be blank"
    if not len(self.account_number.strip()) > 0: 
      errors['account_number'] = "account number can not be blank"
    if self.account_type is None: 
      errors['account_type'] = "account type can not be empty"
    if not (self.parent is None or self._state.adding == False or self.parent.inactive == False):
      errors['parent'] = "can't create child for inactive parent"
    if self.parent and not self.account_number.startswith(f'{self.parent.account_number}.'):
      errors['account_number'] = f"account number should have the prefix {self.parent.account_number}."
    if self.parent and self.account_type != self.parent.account_type:
      errors['account_type'] = f"account type should be same as parent's account type"
    if self.parent and self.parent.inactive == True and self.inactive == False:
      errors['inactive'] = "Can't make an account active if parent is inactive"
    if errors:
      raise ValidationError(errors)

  def save(self, **kwargs):
    with transaction.atomic():
      super(Account, self).save(**kwargs)
      if self._inactive_changed:
        Account.objects.filter(account_number__startswith=self.account_number).update(inactive=self.inactive)
        self._inactive_changed = False

  def __str__(self):
    return f"{self.account_number} - {self.name}"

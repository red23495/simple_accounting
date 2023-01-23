from django import forms
from .models import Account
from django.core.exceptions import ValidationError
from accounting.utils import non_empty_validator, non_zero_validator

class AccountForm(forms.ModelForm):

  name = forms.CharField(validators=[non_empty_validator])
  account_number = forms.CharField(validators=[non_empty_validator])

  def clean(self):
    cleaned_data = super().clean()
    parent: Account = cleaned_data.get('parent')
    account_number: str = cleaned_data.get('account_number')
    account_type: int = cleaned_data.get('account_type')
    inactive: bool = cleaned_data.get('inactive')
    errors = {}
    if not self.instance and parent and parent.inactive:
      errors['parent'] = "can't create child for inactive parent"
    if parent and not account_number.startswith(f'{parent.account_number}.'):
      errors['account_number'] = f"account number should have the prefix {parent.account_number}."
    if parent and account_type != parent.account_type:
      errors['account_type'] = f"account type should be same as parent's account type"
    if parent and parent.inactive == True and inactive == False:
      errors['parent'] = "Can't make an account active if parent is inactive"
    if errors:
      raise ValidationError(errors)
    return cleaned_data

  class Meta:
    fields = '__all__'
    model = Account


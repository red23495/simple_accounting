from django import forms
from .models import Account, non_empty_validator, VoucherType, Voucher, Ledger
from django.core.exceptions import ValidationError

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


class VoucherTypeForm(forms.ModelForm):

  class Meta:
    fields = '__all__'
    model = VoucherType


class VoucherForm(forms.ModelForm):

  class Meta:
    fields = '__all__'
    model = Voucher

class LedgerForm(forms.ModelForm):

  class Meta:
    fields = '__all__'
    model = Ledger

class _LedgerInlineFormset(forms.BaseInlineFormSet):

  def clean(self):
    super().clean()
    debit = 0
    credit = 0
    for form in self.forms:
      cleaned_data = form.clean()
      if not form.is_valid() or not cleaned_data:
        continue
      amount = cleaned_data.get('amount')
      account = cleaned_data.get('account')
      account_type = account.account_type if account else None
      if amount > 0:
        if account_type in [Account.AccountTypes.ASSET, Account.AccountTypes.EXPENSE]:
          debit += amount
        else:
          credit += amount
      elif amount < 0:
        if account_type in [Account.AccountTypes.LIABILITY, Account.AccountTypes.EQUITY, Account.AccountTypes.REVENUE]:
          debit += amount
        else:
          credit += amount
    if debit != credit:
      raise ValidationError('Debit Credit must be equal')

LedgerInlineFormset = forms.inlineformset_factory(Voucher, Ledger, form=LedgerForm, formset=_LedgerInlineFormset)
from django import forms
from .models import VoucherType, Voucher, Ledger
from accounting.utils import non_empty_validator, non_zero_validator
from accounting.account.models import Account
from django.core.exceptions import ValidationError

class VoucherTypeForm(forms.ModelForm):

  name = forms.CharField(validators=[non_empty_validator])
  prefix = forms.CharField(validators=[non_empty_validator])

  class Meta:
    fields = '__all__'
    model = VoucherType


class VoucherForm(forms.ModelForm):

  class Meta:
    fields = '__all__'
    model = Voucher



class LedgerForm(forms.ModelForm):

  amount = forms.DecimalField(validators=[non_zero_validator])
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
      if not form.is_valid() or not cleaned_data or cleaned_data.get('DELETE'):
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
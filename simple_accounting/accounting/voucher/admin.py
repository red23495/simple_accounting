from django.contrib import admin
from .models import Ledger
from .forms import VoucherTypeForm, VoucherForm, LedgerInlineFormset, LedgerForm

class VoucherTypeAdmin(admin.ModelAdmin):
  form = VoucherTypeForm

class LedgerInline(admin.TabularInline):
  model = Ledger
  form = LedgerForm
  formset = LedgerInlineFormset

class VoucherAdmin(admin.ModelAdmin):
  list_display = ('__str__', 'voucher_date', 'amount')
  ordering = ('voucher_number',)
  inlines = [LedgerInline]
  form = VoucherForm
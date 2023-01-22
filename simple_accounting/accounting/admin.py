from django.contrib import admin, messages
from .models import Account, Voucher, VoucherType, Ledger
from django.db import transaction
from django.core.exceptions import ValidationError

class AccountActiveListFilter(admin.SimpleListFilter):

  title = 'Active Status'
  parameter_name = 'active'

  def lookups(self, request, model_admin):
    return (
      (1, 'Active'),
      (0, 'Inactive')
    )

  def queryset(self, request, queryset):
    if not self.value():
      return queryset
    return queryset.filter(inactive = self.value()=='0')

class AccountAdmin(admin.ModelAdmin):
  fieldsets = [
    (
      "Account Info", {
        "fields": ('name', 'parent', 'account_type', 'account_number', 'description', 'inactive')
      }
    )
  ]
  list_display = ('__str__', 'account_type', 'is_active')
  list_display_links = ('__str__',)
  ordering = ('account_number',)
  list_filter = ('account_type', AccountActiveListFilter,)
  search_fields = ('name', 'account_number',)
  autocomplete_fields=('parent',)
  actions = ('make_active', 'make_inactive',)

  def is_active(self, account):
    return not account.inactive
  
  is_active.short_description = 'Active'
  is_active.boolean = True

  def set_inactive(self, request, queryset, value: bool):
    with transaction.atomic():
      models = queryset.order_by('account_number').all()
      failed = 0
      for model in models:
        try:
          model.inactive = value
          model.full_clean()
          model.save()
        except ValidationError:
          failed += 1
      if failed:
        self.message_user(request, f"failed to update {failed} accounts", level=messages.ERROR)

  def make_active(self, request, queryset):
    self.set_inactive(request, queryset, False)

  def make_inactive(self, request, queryset):
    self.set_inactive(request, queryset, True)

  make_active.short_description = 'Activate'
  make_inactive.short_description = 'Deactivate'


class LedgerInline(admin.TabularInline):
  model = Ledger

class VoucherAdmin(admin.ModelAdmin):
  list_display = ('__str__', 'voucher_date', 'amount')
  ordering = ('voucher_number',)
  inlines = [LedgerInline]

admin.site.register(Account, AccountAdmin)
admin.site.register(VoucherType)
admin.site.register(Voucher, VoucherAdmin)
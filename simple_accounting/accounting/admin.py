from django.contrib import admin
from .models import Account

class AccountAdmin(admin.ModelAdmin):
  fieldsets = [
    (
      "Account Info", {
        "fields": ('name', 'parent', 'account_type', 'account_number', 'description', 'inactive')
      }
    )
  ]
  list_display = ('__str__', 'account_type', 'inactive')
  list_display_links = ('__str__',)
  ordering = ('account_number',)

admin.site.register(Account, AccountAdmin)
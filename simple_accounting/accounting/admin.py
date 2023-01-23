from django.contrib import admin
from .models import Account, Voucher, VoucherType

from .account.admin import AccountAdmin
from .voucher.admin import VoucherTypeAdmin, VoucherAdmin

admin.site.register(Account, AccountAdmin)
admin.site.register(VoucherType, VoucherTypeAdmin)
admin.site.register(Voucher, VoucherAdmin)
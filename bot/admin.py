from django.contrib import admin
from .models import *


class TelegramUserAdmin(admin.ModelAdmin):
    search_fields = ('user_id', 'username')


admin.site.register(Comment)
admin.site.register(TelegramUser, TelegramUserAdmin)
admin.site.register(PaymentCrypto)
admin.site.register(City)
admin.site.register(Product)
admin.site.register(Pack)
admin.site.register(Area)
admin.site.register(Exchange)

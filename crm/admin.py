from django.contrib import admin
from .models import Member, MemberItem

# Register your models here.

class MemberView(admin.ModelAdmin):
    list_display =('username', 'number', 'enabled', 'memberlevel')
    ordering = ('-updated', '-created')

class MemberItemView(admin.ModelAdmin):
    list_display =('name', 'qty', 'status')
    ordering = ('-updated', '-created')    

admin.site.register(Member, MemberView)
admin.site.register(MemberItem, MemberItemView)
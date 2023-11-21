from django.contrib import admin
from .models import Member

# Register your models here.

class MemberView(admin.ModelAdmin):
    list_display =('username', 'number', 'enabled', 'memberlevel')
    ordering = ('-updated', '-created')

admin.site.register(Member, MemberView)
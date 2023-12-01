from django.contrib import admin
from .models import Member, MemberItem, Type, Category

# Register your models here.

class MemberView(admin.ModelAdmin):
    list_display =('username', 'number', 'enabled', 'memberlevel')
    ordering = ('-updated', '-created')

class MemberItemView(admin.ModelAdmin):
    list_display =('name', 'qty', 'status')
    ordering = ('-updated', '-created')    

class TypeView(admin.ModelAdmin):
    list_display =('company', 'name', 'description')
    ordering = ('company', 'name')
    
class CategoryView(admin.ModelAdmin):
    list_display =('company', 'name', 'description')
    ordering = ('company', 'name')

admin.site.register(Member, MemberView)
admin.site.register(MemberItem, MemberItemView)
admin.site.register(Type, TypeView)
admin.site.register(Category, CategoryView)
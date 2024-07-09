from django.contrib import admin
from .models import Company, Product_Type, Category, Supplier, Product
from .models import Member, MemberItem, CRMAdmin, Customer
from .models import Quotation, Quotation_item, Inventory, PushMessage

# Register your models here.
class CompanyView(admin.ModelAdmin):
    list_display =('ccode', 'name', 'enabled')
    ordering = ('name',)
class Product_TypeView(admin.ModelAdmin):
    list_display =('company', 'name', 'description')
    ordering = ('company', 'name')
    
class CategoryView(admin.ModelAdmin):
    list_display =('company', 'name', 'description')
    ordering = ('company', 'name')

class SupplierView(admin.ModelAdmin):
    list_display =('supplier_company', 'contact', 'phone', 'email')
    # ordering = ('supplier_company')

class ProductView(admin.ModelAdmin):
    list_display =('company', 'name', 'description', 'category', 'product_type', 'status', 'price')
    ordering = ('company', 'name')

class MemberItemView(admin.ModelAdmin):
    list_display =('name', 'company', 'qty', 'status', 'enabled')
    ordering = ('-updated', '-created') 

class MemberView(admin.ModelAdmin):
    list_display =('username', 'number', 'enabled', 'memberlevel')
    ordering = ('-updated', '-created')

class CRMAdminView(admin.ModelAdmin):
    list_display =('company', 'member_enabled', 'quotation_enabled', 'inventory_enabled')

class CustomerView(admin.ModelAdmin):
    list_display =('company', 'customer_company', 'contact', 'phone', 'sales')
    # ordering = ('customer_company')

class QuotationView(admin.ModelAdmin):
    list_display =('company', 'customer_company', 'sales', 'quotation_status', 'total')
    ordering = ('-updated', '-created')

class Quotation_itemView(admin.ModelAdmin):
    list_display =('quotation', 'product', 'quantity', 'price', 'sub_total')
    ordering = ('-updated', '-created')
class InventoryView(admin.ModelAdmin):
    list_display =('company', 'branch', 'product', 'quantity', 'status')
    ordering = ('-updated', '-created')

class PushMessageView(admin.ModelAdmin):
    list_display =('company', 'msgtype', 'message', 'updated')

admin.site.register(Company, CompanyView)
admin.site.register(Product_Type, Product_TypeView)
admin.site.register(Category, CategoryView)
admin.site.register(Supplier, SupplierView)
admin.site.register(Product, ProductView)
admin.site.register(MemberItem, MemberItemView)
admin.site.register(Member, MemberView)
admin.site.register(CRMAdmin, CRMAdminView)
admin.site.register(Customer, CustomerView)
admin.site.register(Quotation, QuotationView)
admin.site.register(Quotation_item, Quotation_itemView)
admin.site.register(Inventory, InventoryView)
admin.site.register(PushMessage, PushMessageView)
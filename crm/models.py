from django.db import models
from django.contrib.auth.models import User
from base.models import Branch
from datetime import timedelta
import django.utils.html
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Create your models here.


pMsgType = [
       ('NEWS', ('Member news / discount')),
       ('Q', ('Quotation or Invoice to be confirmed')),
    ]


class Company(models.Model):
    ccode = models.CharField(max_length=200, null=False, unique=True)
    enabled = models.BooleanField(default=True)
    branchs = models.ManyToManyField(Branch, related_name='branchs',  blank=True, help_text='Branch access rights',)

    name = models.TextField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    contact_person = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=False, blank=False) 
    def __str__(self):
        return self.ccode + '-' + self.name


class Product_Type(models.Model):
    # default 'product' or 'service'
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.name

class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    # product_type = models.ForeignKey(Product_Type, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, default='')

    def __str__(self):
        return self.name

class Supplier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.CharField(max_length=200)
    supplier_company = models.CharField(max_length=200)
    website = models.CharField(max_length=200)    
    address = models.TextField(null=True, blank=True, default='')
    phone = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True, default='')

    def __str__(self):
        return self.supplier_company


# Model for Products and Services
class Product(models.Model):
    class STATUS(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        DELETED = 'deleted', _('Deleted')
        SOLDOUT = 'soldout', _('Sold out')
        OUTOFSTOCK = 'outofstock', _('Out of stock')
        RESERVED = 'reserved', _('Reserved')
        PENDING = 'pending', _('Pending')


    # item_status_choices = [('active', ('active')),
    #                     ('inactive', ('inactive')),
    #                     ('deleted', ('deleted')),
    #                     ('soldout', ('soldout')),
    #                     ('outofstock', ('outofstock')),
    #                     ('reserved', ('reserved')),
    #                     ('pending', ('pending'))
    #                     ]
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, default='')
    product_type = models.ForeignKey(Product_Type, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=200, choices=STATUS.choices, default=STATUS.ACTIVE)
    price = models.FloatField(default=0.0)
    duration = models.DurationField(default=timedelta(days=0))
    barcode = models.CharField(max_length=20, blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    dimensions = models.CharField(max_length=50, blank=True, null=True)
    manufacturing_date = models.DateField(blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class MemberItem(models.Model):
    # global item_status_choices
    enabled = models.BooleanField(default=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200, null=False, blank=False)
    des = models.CharField(max_length=200, null=True, blank=True)
    price = models.FloatField(default=0.0)
    discount_price = models.FloatField(default=0.0)
    member_points = models.IntegerField(default=0)
    qty = models.IntegerField(default=0)
    total_qty = models.IntegerField(default=0)
    duration = models.DurationField(default=timedelta(days=0))
    status = models.CharField(max_length=50, choices=Product.STATUS.choices, default=Product.STATUS.ACTIVE)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)

    def __str__(self):
        return self.name

class Member(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=200, null=False, unique=True)
    login = models.BooleanField(default=False, null=False)
    number = models.CharField(max_length=200, null=False, unique=True)
    password = models.CharField(max_length=200, null=False, blank=False)
    verifycode = models.CharField(max_length=200, null=True, blank=True)
    verifycode_date = models.DateTimeField(null=True, blank=True)
    verified = models.BooleanField(default=False, null=False)
    enabled = models.BooleanField(default=True, null=False)
    token = models.CharField(max_length=200, null=True, blank=True)
    tokendate = models.DateTimeField(null=True, blank=True)
    birthday = models.DateTimeField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    memberpoints = models.IntegerField(default=0)
    memberpointtotal = models.IntegerField(default=0)
    memberlevel = models.CharField(max_length=10, null=True, blank=True)
    nickname = models.CharField(max_length=200, null=True, blank=True)
    lastname = models.CharField(max_length=200, null=True, blank=True)
    firstname = models.CharField(max_length=200, null=True, blank=True)    
    mobilephone_country = models.CharField(max_length=200, null=True, blank=True)
    mobilephone = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=False, blank=False) #, unique=True) # unique=True for production
    address = models.CharField(max_length=200, null=True, blank=True)
    remark = models.CharField(max_length=200, null=True, blank=True)
    createdby = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    class Meta:
        # unique_together = ('mobilephone_country', 'mobilephone',)
        unique_together = ('company', 'username',)
    def __str__(self):
        return self.username

class CRMAdmin(models.Model):
    # CRM function is enabled or disabled
    enabled = models.BooleanField(default=True, null=False)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    # Member function is enabled or disabled
    member_enabled = models.BooleanField(default=True, null=False)
    membernumber_next = models.IntegerField(default=1)
    # membernumber_digit is member number digit, e.g. 3 is 001, 4 is 0001 
    # number = 12 ; print(f"{number:03d}")
    membernumber_digit = models.IntegerField(default=3, help_text=escape(mark_safe('Member number digit, e.g. 3 is 001, 4 is 0001')))
    # membernumber_reset is rules for reset member number, e.g. rules:<Y>2024</Y> now is 2023-12-31, when now is 2024-01-01, reset member number to 1
    membernumber_reset = models.CharField(max_length=100, null=True, blank=True, verbose_name='Reset Member Number rules', help_text = escape(mark_safe('Rules for reset member number, e.g. rules:<Y>2024</Y> now is 2023-12-31, when now is 2024-01-01, reset member number to 1')))
    # membernumber_prefix is rules for member number, <TEXT>MEM</TEXT><Y></Y><m></m><d></d><no></no> is Year, Month, Day, Hour, Minute, Second, Number('%Y-%m-%d %H:%M:%S')
    # e.g. <TEXT>MEM</TEXT><Y></Y><no></no> is MEM2023001       
    membernumber_prefix = models.CharField(max_length=100, null=True, blank=True, help_text = escape(mark_safe('Rules for member number, <TEXT>MEM</TEXT><Y></Y><m></m><d></d><H></H><M></M><S></S><no></no> is Year, Month, Day, Hour, Minute, Second, Number (''%Y-%m-%d %H:%M:%S'')')))

    # Quotation function is enabled or disabled
    quotation_enabled = models.BooleanField(default=True, null=False)
    quotationnumber_next = models.IntegerField(default=1)
    # quotationnumber_digit is quotation number digit, e.g. 3 is 001, 4 is 0001 
    # number = 12 ; print(f"{number:03d}")
    quotationnumber_digit = models.IntegerField(default=3)
    # quotationnumber_reset is rules for reset quotation number, e.g. rules:<Y>2024</Y> now is 2023-12-31, when now is 2024-01-01, reset member number to 1
    quotationnumber_reset = models.CharField(max_length=100, null=True, blank=True)
    # quotationnumber_prefix is rules for quotation number, <TEXT>Q-</TEXT><Y></Y><m></m><d></d><H></H><M></M><S></S><no></no> is Year, Month, Day, Hour, Minute, Second, Number('%Y-%m-%d %H:%M:%S')
    # e.g. <TEXT>Q-</TEXT><Y></Y><no></no> is Q-2023001    
    quotationnumber_prefix = models.CharField(max_length=100, null=True, blank=True)
    quotation_default_terms = models.TextField(max_length=200, null=True, blank=True)
    quotation_default_remark = models.TextField(max_length=200, null=True, blank=True)

    # Inventory function is enabled or disabled
    inventory_enabled = models.BooleanField(default=True, null=False)

    def __str__(self):
        return self.company.name  
    
class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    customer_company = models.CharField(max_length=200, null=True, blank=True)
    contact = models.CharField(max_length=200, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=False, blank=False) 
    referby = models.CharField(max_length=200, null=True, blank=True)
    sales = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    remark = models.CharField(max_length=200, null=True, blank=True)
    createdby = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_createdby')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)

    def __str__(self):
        return self.company

class Quotation(models.Model):
    class STATUS(models.TextChoices):
        FREE = 'free', _('Free, when a quote is created')
        APPROVED = 'approved', _('Approved, when the quote is approved internally. The quote can be printed and sent to the customer')
        PRINTED = 'printed', _('Printed, When a quote is printed as an external document and sent to a customer for review.')
        NEGOTIATING = 'negotiating', _('Indicates that the negotiations about the selected quote are in progress. This status must be set manually')
        ACCEPTED = 'accepted', _('Accepted, after the customer accepts the quote.')
        REJECTED = 'rejected', _('Rejected, indicates that the proposed Quote has been rejected by the customer')
        PROCESSED = 'processed', _('Processed, after the customer accepts the proposal, use the option Process in the appropriate menu to create a maintenance sales order from the quote data.')
        CANCELED = 'canceled', _('Canceled, indicates that the quote is cancelled. Only the quotes with the status Free, Printed or Negotiating can be cancelled')
        LOST = 'lost', _('Lost, indicates that the customer has selected another supplier. This status must be set manually.')



    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    number = models.CharField(max_length=200)
    version = models.CharField(max_length=200, null=True, blank=True)
    quotation_date = models.DateTimeField(auto_now_add=True)    
    quotation_status = models.CharField(max_length=200, choices=STATUS.choices, default=STATUS.FREE)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    customer_company = models.CharField(max_length=200, null=True, blank=True)
    customer_contact = models.CharField(max_length=200, null=True, blank=True)
    customer_phone = models.CharField(max_length=200, null=True, blank=True)
    customer_email = models.EmailField(null=False, blank=False)
    sales = models.CharField(max_length=200, null=True, blank=True)
    confirm_date = models.DateTimeField(null=True, blank=True)
    confirm_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirm_by')
    remark = models.CharField(max_length=200, null=True, blank=True)
    terms = models.CharField(max_length=200, null=True, blank=True)    
    total = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.number
    def unique_together(self):
        return ('company', 'number')
    
class Quotation_item(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    index = models.IntegerField()
    name = models.CharField(max_length=200)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.FloatField(default=0.0)
    sub_total = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    updated = models.DateTimeField(auto_now=True)
class Inventory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    min_quantity = models.IntegerField()
    max_quantity = models.IntegerField()
    status = models.CharField(max_length=200, choices=Product.STATUS.choices, default=Product.STATUS.ACTIVE)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.name
    def unique_together(self):
        return ('branch', 'product',)

class PushMessage(models.Model):

    pushid = models.CharField(max_length=200, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)    
    msgtype = models.CharField(max_length=32, choices=pMsgType, default='NEWS')
    message = models.TextField(null=False, blank=False)
    content = models.TextField(null=True, blank=True)
    imageurl = models.CharField(max_length=200, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)
    updated = models.DateTimeField(auto_now=True)


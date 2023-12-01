from django.db import models
from django.contrib.auth.models import User
from base.models import Branch, Company
# Create your models here.

item_status_choices = [('active', ('active')),
                        ('inactive', ('inactive')),
                        ('deleted', ('deleted')),
                        ('soldout', ('soldout')),
                        ('outofstock', ('outofstock')),
                        ('reserved', ('reserved')),
                        ('pending', ('pending'))
                        ]
q_status_choices = [('free', ('When a quote is created, the status is Free')),
                    ('approved', ('When the quote is approved internally, the status is set to Approved. The quote can be printed and sent to the customer')),
                    ('printed', ('When a quote is printed as an external document and sent to a customer for review, the status of the quote is changed to Printed')),
                    ('negotiating', ('Indicates that the negotiations about the selected quote are in progress. This status must be set manually')),
                    ('accepted', ('After the customer accepts the quote, the status of the quote changes to Accepted')),
                    ('rejected', ('Indicates that the proposed Quote has been rejected by the customer')),
                    ('processed', ('After the customer accepts the proposal, use the option Process in the appropriate menu to create a maintenance sales order from the quote data. The status of the quote changes to Processed. All the quote lines that are linked to the quote are copied to the maintenance sales order as Part Maintenance Lines')),
                    ('canceled', ('Indicates that the quote is cancelled. Only the quotes with the status Free, Printed or Negotiating can be cancelled')),
                    ('lost', ('Indicates that the customer has selected another supplier. This status must be set manually. This status is applicable only for Quotes that are not generated from another object')),
                    ]




class Type(models.Model):
    # default 'product' or 'service'
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.name

class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.name

class Supplier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    person = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    website = models.CharField(max_length=200)    
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.name


# Model for Products and Services
class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    product_type = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=200, choices=item_status_choices, default='active')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    min_quantity = models.IntegerField()
    duration = models.DurationField()
    barcode = models.CharField(max_length=20, blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
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
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200, null=False, blank=False)
    des = models.CharField(max_length=200, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)
    member_points = models.IntegerField(default=0)
    qty = models.IntegerField(default=0)
    status = models.CharField(max_length=200, choices=item_status_choices, default='active')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)

    def __str__(self):
        return self.name

class Member(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=200, null=False, unique=True)
    number = models.CharField(max_length=200, null=False, unique=True)
    password = models.CharField(max_length=200, null=False, blank=False)
    verifycode = models.CharField(max_length=200, null=True, blank=True)
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
    # class Meta:
    #     unique_together = ('mobilephone_country', 'mobilephone',)  
    def __str__(self):
        return self.username

class MemberAdmin(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    enabled = models.BooleanField(default=True, null=False)
    nextmembernumber = models.IntegerField(default=1)

    def __str__(self):
        return self.branch.bcode    
    
class Customer(models.Model):
    company = models.CharField(max_length=200, null=True, blank=True)
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
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    number = models.CharField(max_length=200)
    version = models.CharField(max_length=200, null=True, blank=True)
    quotation_date = models.DateTimeField(auto_now_add=True)    
    quotation_status = models.CharField(max_length=200, choices=q_status_choices, default='active')
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
    total = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return self.quotation_date
    
class Quotation_item(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    index = models.IntegerField()
    name = models.CharField(max_length=200)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=20, decimal_places=2)
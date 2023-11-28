from django.db import models
from django.contrib.auth.models import User
from base.models import Branch
# Create your models here.

item_status_choices = [('active', ('active')),
                        ('inactive', ('inactive')),
                        ('deleted', ('deleted')),
                        ('soldout', ('soldout')),
                        ('outofstock', ('outofstock')),
                        ('reserved', ('reserved')),
                        ('pending', ('pending'))
                        ]

class Type(models.Model):
    # default 'product' or 'service'
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.name

class Supplier(models.Model):
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
    branchs = models.ManyToManyField(Branch, related_name='branchs')
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
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
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
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
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
    enabled = models.BooleanField(default=True, null=False)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    nextmembernumber = models.IntegerField(default=1)
    def __str__(self):
        return self.branch.bcode    
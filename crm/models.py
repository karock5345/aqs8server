from django.db import models
from django.contrib.auth.models import User
from base.models import Branch
# Create your models here.

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
    memberpoint = models.IntegerField(default=0)
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

from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Member(models.Model):
    number = models.CharField(max_length=200, null=False, unique=True)
    password = models.CharField(max_length=200, null=False)
    verifycode = models.CharField(max_length=200, null=True)
    enabled = models.BooleanField(default=True, null=False)
    token = models.CharField(max_length=200, null=True)
    tokenexpire = models.DateTimeField(null=True, blank=True)
    birthday = models.DateTimeField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True)
    memberpoint = models.IntegerField(default=0)
    memberpointtotal = models.IntegerField(default=0)
    memberlevel = models.CharField(max_length=10, null=True)
    nickname = models.CharField(max_length=200, null=True)
    lastname = models.CharField(max_length=200, null=True)
    firstname = models.CharField(max_length=200, null=True)    
    mobilephone = models.CharField(max_length=200, null=True)
    mobilephone_country = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    address = models.CharField(max_length=200, null=True)
    remark = models.CharField(max_length=200, null=True)
    createdby = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now_add just auto add once (the first created)


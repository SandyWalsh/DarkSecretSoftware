from django import forms
from django.db import models


class Tenant(models.Model):
    email = models.CharField(max_length=50)
    project_name = models.CharField(max_length=50)
    tenant_id = models.AutoField(primary_key=True, unique=True)


class RawData(models.Model):
    tenant = models.ForeignKey(Tenant, db_index=True,
                               to_field='tenant_id')
    nova_tenant = models.CharField(max_length=50, null=True,
                                   blank=True, db_index=True)
    json = models.TextField()
    routing_key = models.CharField(max_length=50, null=True,
                                   blank=True, db_index=True)
    state = models.CharField(max_length=50, null=True, 
                             blank=True, db_index=True)
    when = models.DateTimeField(db_index=True)
    microseconds = models.IntegerField(default=0)
    publisher = models.CharField(max_length=50, null=True,
                                 blank=True, db_index=True)
    event = models.CharField(max_length=50, null=True,
                                 blank=True, db_index=True)
    service = models.CharField(max_length=50, null=True,
                                 blank=True, db_index=True)
    host = models.CharField(max_length=50, null=True,
                                 blank=True, db_index=True)
    instance = models.CharField(max_length=50, null=True,
                                blank=True, db_index=True)


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ('email', 'project_name')

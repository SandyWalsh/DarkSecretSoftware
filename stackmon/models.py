from django.db import models


class RawData(models.Model):
    tenant = models.IntegerField(default=0)
    json = models.TextField()
    routing_key = models.CharField(max_length=50)
    when = models.DateTimeField()
    publisher = models.CharField(max_length=50)
    host = models.CharField(max_length=50)
    instance = models.CharField(max_length=50)


class KeyValue(models.Model):
    raw_data = models.ForeignKey(RawData)
    key = models.CharField(max_length=50)
    value = models.TextField()

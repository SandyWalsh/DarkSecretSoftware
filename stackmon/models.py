from django.db import models


class RawData(models.Model):
    tenant = models.IntegerField(default=0)
    json = models.TextField()
    routing_key = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    when = models.DateTimeField()
    publisher = models.CharField(max_length=50)
    event = models.CharField(max_length=50)
    service = models.CharField(max_length=50)
    host = models.CharField(max_length=50)
    instance = models.CharField(max_length=50, blank=True)

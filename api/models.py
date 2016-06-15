from __future__ import unicode_literals

from django.db import models

class Instruments(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)
    token = models.CharField(max_length=100)
    tick_size = models.CharField(max_length=100)
    exchange = models.CharField(max_length=100)

    def getDetails(self):
        ret = {}
        ret['id'] = self.id
        ret['name']=self.city
        ret['region']=self.reigon
        return ret

    class Meta:
        managed = True
        db_table = 'Instruments'
from django.db import models
from django.db.models import Min
from django.conf import settings

import hashlib
from datetime import timedelta

class OAIRepository(models.Model):
    repo_id = models.CharField(max_length=25)
    name = models.CharField(max_length=255)

    def get_earliest_datestamp(self):
        d = self.get_all_records().aggregate(Min('datestamp'))
        return d['datestamp__min'].strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_all_records(self):
        sets = self.oaiset_set.all()
        return OAIRecord.objects.filter(sets__in=sets)

    def __str__(self):
        return self.name

class OAISet(models.Model):
    repository = models.ForeignKey(OAIRepository)
    set_id = models.CharField(max_length=25)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class OAIRecord(models.Model):
    identifier = models.CharField(max_length=255)
    datestamp = models.DateTimeField()
    sets = models.ManyToManyField(OAISet)

    def __str__(self):
        return self.identifier

class OAIField(models.Model):
    record = models.ForeignKey(OAIRecord)
    name = models.CharField(max_length=20)
    value = models.CharField(max_length=255)

    def __str__(self):
        return "{}:{}".format(self.name, self.value)

class ResumptionToken(models.Model):
    date_created = models.DateTimeField(auto_now=True)
    verb = models.CharField(max_length=64)
    set = models.ForeignKey(OAISet, null=True, blank=True)
    fro = models.DateTimeField(null=True, blank=True)
    until = models.DateTimeField(null=True, blank=True)
    cursor = models.IntegerField()
    first_timestamp = models.DateTimeField()
    key = models.CharField(max_length=128, null=True, blank=True)

    def expiration_date(self):
        return self.date_created + timedelta(days=3)

    def genkey(self):
        m = hashlib.md5()
        m.update("{}_{}_{}_{}_{}_{}_{}".format(settings.OAI_RESUMPTION_TOKEN_SALT, self.date_created, self.id, 
                                               self.set, self.fro, self.until, self.cursor).encode('utf-8'))
        self.key = m.hexdigest()
        self.save(update_fields=['key'])

    def __str__(self):
        return self.key

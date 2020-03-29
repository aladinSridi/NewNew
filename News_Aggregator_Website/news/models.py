# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class article(models.Model):
    reference = models.CharField(max_length=200)
    image_src = models.URLField(null=True, blank=True)
    title = models.TextField(default="")
    link = models.TextField(default="")
    text = models.TextField(default="")
    date = models.DateTimeField()
    category = models.CharField(max_length=200)
    label = models.TextField(default="")

    def __str__(self):
        return self.title

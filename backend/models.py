from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=32, unique=True)


class Category(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)


class Image(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    annotated = models.BooleanField()

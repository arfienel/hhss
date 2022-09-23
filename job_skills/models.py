import datetime
from django.db import models
from django.contrib.auth.models import User


class JobTracker(models.Model):
    user_creator = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    modified_date = models.DateField(auto_now=True)
    search_text = models.CharField(max_length=100)
    status_parser = models.BooleanField(default=False)
    exclude_from_search = models.CharField(max_length=100, default='', blank=True)

    def __repr__(self):
        return f'<Tracker {self.search_text} {self.id}>'


class ParserData(models.Model):
    tracker = models.ForeignKey(JobTracker, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    amount_of_vacancies = models.IntegerField(default=0)
    error_log = models.TextField(default='', blank=True, null=True)

    class Meta:
        ordering = ["-date"]

    def __repr__(self):
        return f'ParserData {self.id}'


class SkillData(models.Model):
    parser_data = models.ForeignKey(ParserData, on_delete=models.CASCADE)
    tracker = models.ForeignKey(JobTracker, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    name = models.CharField(max_length=200)

    def __repr__(self):
        return f'<SkillData {self.name} {self.id}>'

    class Meta:
        ordering = ["-amount", "name"]

import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class JobTracker(models.Model):
    user_creator = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    modified_date = models.DateField(default=now)
    search_text = models.CharField(max_length=100)
    status_parser = models.BooleanField(default=False)
    exclude_from_search = models.CharField(max_length=100, default='', blank=True)
    subscribers = models.ManyToManyField(User, related_name='job_tracker_subs')

    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_date_modify', False):
            self.modified_date = datetime.datetime.now()

        super(JobTracker, self).save(*args, **kwargs)

    def __str__(self):
        return f'<Tracker {self.search_text} {self.id}>'

    def __repr__(self):
        return f'<Tracker {self.search_text} {self.id}>'


class ParserData(models.Model):
    tracker = models.ForeignKey(JobTracker, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    amount_of_vacancies = models.IntegerField(default=0)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f'ParserData {self.tracker.search_text}'

    def __repr__(self):
        return f'ParserData {self.tracker.search_text}'


class SkillData(models.Model):
    parser_data = models.ForeignKey(ParserData, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f'<SkillData {self.name} {self.id}>'

    def __repr__(self):
        return f'<SkillData {self.name} {self.id}>'

    class Meta:
        ordering = ["-amount", "name"]

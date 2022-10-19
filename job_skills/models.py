import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.contrib.postgres.fields import ArrayField


class Area(models.Model):
    hh_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=1000, db_index=True)

    def __str__(self):
        return f'<Area {self.name} {self.hh_id}>'

    class Meta:
        unique_together = ('hh_id', 'name')


class JobTracker(models.Model):
    user_creator = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    modified_date = models.DateField(default=now, db_index=True)
    search_text = models.CharField(max_length=100, db_index=True)
    status_parser = models.BooleanField(default=False)
    exclude_from_search = models.CharField(max_length=100, default='', blank=True)
    hh_url = models.TextField(default='https://hh.ru')
    subscribers = models.ManyToManyField(User, related_name='job_tracker_subs')
    areas = ArrayField(models.IntegerField(), default=[], db_index=True)
    employment_type = ArrayField(models.CharField(max_length=100), default=[], db_index=True)
    work_experience = models.CharField(max_length=100, default='', blank=True, db_index=True)
    work_schedule = ArrayField(models.CharField(max_length=100), default=[], db_index=True)

    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_date_modify', False):
            self.modified_date = datetime.datetime.now()
        print(args, kwargs)
        areas_part = ''.join(f'&area={str(area)}' for area in self.areas)
        work_schedule_part = ''.join(f'&schedule={exp}' for exp in self.work_schedule)
        employment_type_part = ''.join(f'&employment={emp}' for emp in self.employment_type)

        self.hh_url = f"https://hh.ru/search/vacancy?excluded_text={self.exclude_from_search}&search_field=name&" \
                      f"search_field=company_name&search_field=description&text={self.search_text}" \
                      f"&experience={self.work_experience}" \
                      f"{areas_part}" \
                      f"{work_schedule_part}" \
                      f"{employment_type_part}"

        super(JobTracker, self).save(*args, **kwargs)

    def __str__(self):
        return f'<Tracker {self.search_text} {self.id}>'

    def __repr__(self):
        return f'<Tracker {self.search_text} {self.id}>'


class ParserData(models.Model):
    tracker = models.ForeignKey(JobTracker, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True, db_index=True)
    amount_of_vacancies = models.IntegerField(default=0)

    class Meta:
        ordering = ["-date", '-id']

    def __str__(self):
        return f'ParserData {self.tracker.search_text} {self.id}'

    def __repr__(self):
        return f'ParserData {self.tracker.search_text} {self.id}'


class SkillData(models.Model):
    parser_data = models.ForeignKey(ParserData, on_delete=models.CASCADE, db_index=True)
    amount = models.IntegerField(default=0)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f'<SkillData {self.name} {self.parser_data.id}>'

    def __repr__(self):
        return f'<SkillData {self.name} {self.parser_data.id}>'

    class Meta:
        ordering = ["-amount", "name"]

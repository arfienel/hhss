from django.contrib import admin
from .models import *


class JobTrackerAdmin(admin.ModelAdmin):
    list_display = ('id', 'search_text', 'exclude_from_search', 'user_creator', 'modified_date',)
    search_fields = ('id', 'search_text',)


class SkillDataAdmin(admin.ModelAdmin):
    search_fields = ('parser_data__id',)
    list_display = ('parser_data', 'amount', 'name',)


class ParserDataAdmin(admin.ModelAdmin):
    search_fields = ('id', 'tracker.search_text', 'tracker.id')
    list_display = ('id', 'tracker', 'date', 'amount_of_vacancies',)


admin.site.register(JobTracker, JobTrackerAdmin)
admin.site.register(SkillData, SkillDataAdmin)
admin.site.register(ParserData, ParserDataAdmin)
admin.site.register(Area)
# Register your models here.

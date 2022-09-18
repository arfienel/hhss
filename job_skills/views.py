from datetime import datetime
import asyncio
import threading
from django.shortcuts import render, HttpResponse, redirect
from .models import *
from .hh_parser import parse_one_tracker


def index(request):
    trackers = JobTracker.objects.all()
    parsers_all = ParserData.objects.all()
    parsers = {}
    for tracker in trackers:
        try:
            parsers[tracker.id] = parsers_all.filter(tracker_id=tracker.id)[0]
        except IndexError:
            pass
    skills = {}
    skills_all = SkillData.objects.all()
    for parser in parsers:
        parser_id = parsers[parser].id
        skills[parser_id] = skills_all.filter(parser_data_id=parser_id)
    context = {
        'trackers': trackers,
        'parsers': parsers,
        'skills': skills,
    }
    return render(request, 'index.html', context)


def create_tracker(request):
    search_text = request.POST['search_text']
    exclude_from_search = request.POST['exclude_from_search']
    new_job_tracker = JobTracker(search_text=search_text, exclude_from_search=exclude_from_search)
    new_job_tracker.save()
    thread = threading.Thread(target=parse_one_tracker, args=[new_job_tracker.id])
    thread.start()
    return redirect('index')


def delete_tracker(request):
    tracker_to_delete = JobTracker.objects.get(id=request.POST['tracker_id'])
    tracker_to_delete.delete()
    return HttpResponse(f'Successfully deleted {tracker_to_delete.id, tracker_to_delete.search_text}')


def update_tracker(request):
    tracker_to_update = JobTracker.objects.get(id=request.POST['tracker_id'])
    tracker_to_update.search_text = request.POST['search_text']
    tracker_to_update.exclude_from_search = request.POST['exclude_from_search']
    tracker_to_update.save()
    return HttpResponse(f'Successfully updated {tracker_to_update.id, tracker_to_update.search_text}')

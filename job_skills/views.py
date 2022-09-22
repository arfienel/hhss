from datetime import datetime as dt
from datetime import timedelta
import asyncio
import threading
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect, reverse
from django.http import HttpResponseNotAllowed
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import *
from .hh_parser import parse_one_tracker
from .forms import UserRegistrationForm


def index(request):
    if request.session.get('error_message'):
        messages.error(request, str(request.session.get('error_message')))
        del request.session['error_message']

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
    if request.method == "POST":
        search_text = request.POST['search_text']
        exclude_from_search = request.POST['exclude_from_search']
        new_job_tracker = JobTracker(search_text=search_text, exclude_from_search=exclude_from_search,
                                     user_creator=request.user)
        new_job_tracker.save()
        thread = threading.Thread(target=parse_one_tracker, args=[new_job_tracker.id])
        thread.start()
        return redirect('index')
    else:
        raise HttpResponseNotAllowed


def delete_tracker(request):
    if request.method == "POST":
        tracker_to_delete = JobTracker.objects.get(id=request.POST['tracker_id'])
        today = dt.today().date()
        date_difference = today - tracker_to_delete.modified_date
        if date_difference < timedelta(days=3):
            request.session['error_message'] = f'wait {str((timedelta(days=3) - date_difference).days)} days, before delete tracker'
            return HttpResponse(request.session['error_message'])
        tracker_to_delete.delete()
        return HttpResponse(f'Successfully deleted {tracker_to_delete.id, tracker_to_delete.search_text}')
    else:
        raise HttpResponseNotAllowed


def update_tracker(request):
    if request.method == "POST":
        tracker_to_update = JobTracker.objects.get(id=request.POST['tracker_id'])
        today = dt.today().date()
        date_difference = today - tracker_to_update.modified_date
        if date_difference < timedelta(days=3):
            request.session['error_message'] = f'wait {str((timedelta(days=3) - date_difference).days)} days, before update tracker'
            return HttpResponse(request.session['error_message'])
        tracker_to_update.search_text = request.POST['search_text']
        tracker_to_update.exclude_from_search = request.POST['exclude_from_search']
        tracker_to_update.save()
        return HttpResponse(f'Successfully updated {tracker_to_update.id, tracker_to_update.search_text}')
    else:
        raise HttpResponseNotAllowed


def registration(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username=form.cleaned_data['username'],
                                            password=form.cleaned_data['password'],
                                            email=form.cleaned_data['email'])
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            return redirect('index')
        else:
            return render(request, 'registration/registration.html', context={'form': form})
    elif request.method == "GET":
        return render(request, 'registration/registration.html', context={'form': UserRegistrationForm()})


def user_logout(request):
    logout(request)
    return redirect('index')

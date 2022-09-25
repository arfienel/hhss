from datetime import datetime as dt
from datetime import timedelta
import asyncio
import threading
import json
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect, reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.serializers import serialize
from .models import *
from .hh_parser import parse_one_tracker
from .forms import UserRegistrationForm


def index(request):
    if request.session.get('error_message'):
        messages.error(request, str(request.session.get('error_message')))
        del request.session['error_message']
    if request.user.is_authenticated:
        trackers = JobTracker.objects.filter(user_creator=request.user.id)
        parsers_all = ParserData.objects.filter(tracker_id__user_creator=request.user.id)
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
    else:
        context = {

        }
    return render(request, 'index.html', context)


def list_trackers(request):
    if request.GET.get('search'):
        search_field = request.GET.get('search')
    else:
        search_field = ''
    trackers_parsers = []
    trackers = JobTracker.objects.filter(search_text__icontains=search_field)[:6]
    for tracker in trackers:
        parser = ParserData.objects.filter(tracker_id=tracker.id)[0].__dict__
        skills = SkillData.objects.filter(parser_data=parser['id'])[:3].values()
        trackers_parsers.append((tracker.__dict__, parser, skills))
    return render(request, 'list_trackers.html', {'trackers_parsers': trackers_parsers})


def list_more_trackers(request):
    if request.GET.get('search'):
        search_field = request.GET.get('search')
    else:
        search_field = ''

    if request.GET.get('page'):
        page = int(request.GET.get('page'))
    else:
        page = 1
    print(page)
    data = []
    trackers = JobTracker.objects.filter(search_text__icontains=search_field)[page*6:page*6+6]

    for tracker in trackers:
        parser = ParserData.objects.filter(tracker_id=tracker.id)[:1]
        skills = SkillData.objects.filter(parser_data=parser[0].id)[:3]
        data.append((serialize('json', [tracker, ]), serialize('json', parser), serialize('json', skills)))
    print(data)
    return JsonResponse(data, safe=False, content_type='application/json')


def load_parser_data(request):
    tracker = JobTracker.objects.get(pk=request.GET.get('tracker_id'))
    last_parser_data = ParserData.objects.filter(tracker_id=tracker.id)[0]
    skills = SkillData.objects.filter(parser_data=last_parser_data.id).values('name', 'amount')
    return HttpResponse(json.dumps(list(skills)), content_type='application/json')


@login_required
def create_tracker(request):
    if request.method == "POST":
        if JobTracker.objects.filter(user_creator=request.user.id).count() >= 5:
            if request.user.is_staff:
                request.session['error_message'] = 'Understandable, have a great day!'
            else:
                request.session['error_message'] = 'You already created 5 trackers, which is maximum, try to delete or update other trackers'
                return redirect('index')

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


@login_required
def delete_tracker(request):
    if request.method == "POST":
        tracker_to_delete = JobTracker.objects.get(id=request.POST['tracker_id'])

        if request.user.id != tracker_to_delete.user_creator.id:
            request.session['error_message'] = f'forbidden operation'
            return HttpResponse(request.session['error_message'])

        today = dt.today().date()
        date_difference = today - tracker_to_delete.modified_date
        if date_difference <= timedelta(days=3):
            request.session['error_message'] = f'wait {str((timedelta(days=3) - date_difference).days)} days, before delete tracker'
            return HttpResponse(request.session['error_message'])

        tracker_to_delete.delete()
        return HttpResponse(f'Successfully deleted {tracker_to_delete.id, tracker_to_delete.search_text}')
    else:
        raise HttpResponseNotAllowed


@login_required
def update_tracker(request):
    if request.method == "POST":
        tracker_to_update = JobTracker.objects.get(id=request.POST['tracker_id'])

        if request.user.id != tracker_to_update.user_creator.id:
            request.session['error_message'] = f'forbidden operation'
            return HttpResponse(request.session['error_message'])

        today = dt.today().date()
        date_difference = today - tracker_to_update.modified_date
        if date_difference <= timedelta(days=3):
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

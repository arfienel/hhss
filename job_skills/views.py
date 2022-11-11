import asyncio
import threading
import json
import logging
from datetime import datetime as dt
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect, reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.core.serializers import serialize
from django.contrib.auth.models import User
from rest_framework import views
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from .models import *
from .hh_parser import parse_one_tracker
from .forms import UserRegistrationForm
from .serializers import TrackerSerializer, AreaSerializer
from .permissions import IsOwnerOrReadOnly


def index(request):
    if request.session.get('error_message'):
        messages.error(request, str(request.session.get('error_message')))
        del request.session['error_message']
    if request.user.is_authenticated:
        trackers = JobTracker.objects.filter(Q(user_creator=request.user.id) | Q(subscribers__in=(request.user.id,)))
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

        subscribed_trackers = []
        for tracker in trackers:
            if request.user.id in [sub[0] for sub in tracker.subscribers.values_list('id')]:
                subscribed_trackers.append(tracker)
                trackers = trackers.exclude(pk=tracker.id)

        context = {
            'subscribed_trackers': subscribed_trackers,
            'trackers': trackers,
            'parsers': parsers,
            'skills': skills,
            'areas': Area.objects.order_by('name').all()
        }
    else:
        context = {
            'subscribed_trackers': [],
            'trackers': [],
            'parsers': [],
            'skills': [],
        }
    return render(request, 'index.html', context)


def list_trackers(request):
    if request.GET.get('search'):
        search_field = request.GET.get('search')
    else:
        search_field = ''
    trackers_parsers = []
    trackers = JobTracker.objects.filter(search_text__icontains=search_field).order_by('-modified_date', 'pk')[:6].all()

    for tracker in trackers:
        try:
            tracker_to_append = tracker.__dict__
            tracker_to_append['subscribers'] = [sub[0] for sub in tracker.subscribers.values_list('id')]
            areas = Area.objects.filter(hh_id__in=tracker.areas)
            parser = ParserData.objects.filter(tracker_id=tracker.id)[0].__dict__
            skills = SkillData.objects.filter(parser_data=parser['id'])[:3].values()
            trackers_parsers.append((tracker_to_append, parser, skills, areas))
        except IndexError:
            # logger ebanut suda
            pass
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

    data = []
    trackers = JobTracker.objects.filter(search_text__icontains=search_field).order_by('-modified_date', 'pk')[page*6:page*6+6].all()

    for tracker in trackers:
        try:
            areas = Area.objects.filter(hh_id__in=tracker.areas)
            parser = ParserData.objects.filter(tracker_id=tracker.id)[:1]
            skills = SkillData.objects.filter(parser_data=parser[0].id)[:3]
            data.append((serialize('json', [tracker, ]), serialize('json', parser), serialize('json', skills), serialize('json', areas)))
        except Exception as exc:
            print(exc)
    return JsonResponse(data, safe=False, content_type='application/json')


def load_parser_data(request):
    tracker = JobTracker.objects.get(pk=request.GET.get('tracker_id'))
    last_parser_data = ParserData.objects.filter(tracker_id=tracker.id)[0]
    skills = SkillData.objects.filter(parser_data=last_parser_data.id).values('name', 'amount')
    return HttpResponse(json.dumps(list(skills)), content_type='application/json')


@login_required
def subscribe_on_tracker(request):
    if request.method == "POST":
        tracker = JobTracker.objects.get(id=request.POST['tracker_id'])
        tracker.subscribers.add(request.user)
        tracker.save(skip_date_modify=True)
        return HttpResponse('good')


def unsubscribe_from_tracker(request):
    if request.method == "POST":
        tracker = JobTracker.objects.get(id=request.POST['tracker_id'])
        tracker.subscribers.remove(request.user)
        tracker.save(skip_date_modify=True)
        return HttpResponse('good')


def validate_search_text(request):
    search_text = request.POST['search_text']
    if len(search_text) < 2:
        if any(['js', '1c', '1с', 'c#']) == search_text.lower():
            pass
        else:
            request.session['error_message'] = str(_('minimum 3 letters'))
            return 0

    return search_text


def validate_areas(request):
    try:
        if 'area[]' in request.POST:
            area = request.POST.getlist('area[]')
        else:
            area = []
        areas = [int(ar) for ar in area]
    except Exception as exc:
        print(exc)
        request.session['error_message'] = str(_('incorrectly selected areas'))
        return 0
    else:
        return areas


def validate_work_schedule(request):
    try:
        if 'timetable[]' in request.POST:
            timetable = request.POST.getlist('timetable[]')
        else:
            timetable = []
        timetables = [str(ar) for ar in timetable]
    except Exception as exc:
        # добавить логгер и ошибки попроавить
        print(exc)
        request.session['error_message'] = str(_('incorrectly selected work schedule'))
        return 0
    else:
        return timetables


def validate_employment_type(request):
    try:
        if 'employment-type[]' in request.POST:
            employment_type = request.POST.getlist('employment-type[]')
        else:
            employment_type = []
        employment_types = [str(ar) for ar in employment_type]
    except Exception as exc:
        # добавить логгер и ошибки попроавить
        print(exc)
        request.session['error_message'] = str(_('incorrectly selected employment types'))
        return 0
    else:
        return employment_types

@login_required
def create_tracker(request):
    if request.method == "POST":
        if JobTracker.objects.filter(user_creator=request.user.id).count() >= 5:
            if request.user.is_staff:
                request.session['error_message'] = str(_('Understandable, have a great day!'))
            else:
                request.session['error_message'] = str(_('You already created 5 trackers, which is maximum, try to delete or update other trackers'))
                return redirect('index')
        new_job_tracker = JobTracker()
        new_job_tracker.search_text = validate_search_text(request)
        new_job_tracker.areas = validate_areas(request)
        new_job_tracker.work_schedule = validate_work_schedule(request)
        new_job_tracker.employment_type = validate_employment_type(request)
        if new_job_tracker.search_text == 0 or new_job_tracker.areas == 0 or new_job_tracker.work_schedule == 0 or new_job_tracker.employment_type == 0:
            return redirect('index')
        new_job_tracker.exclude_from_search = request.POST['exclude_from_search']
        new_job_tracker.work_experience = request.POST['work-experience']
        new_job_tracker.user_creator = request.user
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
        if request.user.is_staff:
            pass
        elif date_difference <= timedelta(days=3):
            request.session['error_message'] = _('days, before delete tracker') + f' {int((timedelta(days=3) - date_difference).days)}'
            print(request.session['error_message'])
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
        if request.user.is_staff:
            pass
        elif date_difference <= timedelta(days=3):
            request.session['error_message'] = str(_('wait')) + f'{str((timedelta(days=3) - date_difference).days)}' + str(_(' days, before update tracker'))
            return HttpResponse(request.session['error_message'])
        tracker_to_update.search_text = validate_search_text(request)
        tracker_to_update.areas = validate_areas(request)
        tracker_to_update.work_schedule = validate_work_schedule(request)
        tracker_to_update.employment_type = validate_employment_type(request)
        if tracker_to_update.search_text == 0 or tracker_to_update.areas == 0 or tracker_to_update.work_schedule == 0 or tracker_to_update.employment_type == 0:
            return redirect('index')
        tracker_to_update.work_experience = request.POST['work-experience']
        tracker_to_update.exclude_from_search = request.POST['exclude_from_search']
        tracker_to_update.save()
        thread = threading.Thread(target=parse_one_tracker, args=[tracker_to_update.id])
        thread.start()
        return HttpResponse(f'Successfully updated {tracker_to_update.id, tracker_to_update.search_text}')
    else:
        raise HttpResponseNotAllowed


def registration(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username=form.cleaned_data['username'],
                                            password=form.cleaned_data['password'])
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


# api views (drf)
class JobTrackerView(views.APIView):
    permission_classes = (IsOwnerOrReadOnly, )

    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            if request.user.is_authenticated:
                trackers = JobTracker.objects.filter(user_creator=request.user)
            else:
                trackers = JobTracker.objects.all()
            serializer = TrackerSerializer(trackers, many=True)
            return Response({'tracker': serializer.data})
        else:
            try:
                tracker = JobTracker.objects.get(pk=pk)
            except:
                return Response({"error": "Object does not exists"})
            if 'for_chart' in request.GET:
                parser_data = ParserData.objects.filter(tracker_id=tracker.id).values('date', 'amount_of_vacancies')
                serializer = TrackerSerializer(tracker, many=False)
                response = {'tracker': serializer.data, 'chart_data': parser_data}
                return Response(response)
            else:
                last_parser_data = ParserData.objects.filter(tracker_id=tracker.id)[0]
                skills = SkillData.objects.filter(parser_data=last_parser_data.id).values('name', 'amount')
                serializer = TrackerSerializer(tracker, many=False)
                response = {'tracker': serializer.data, 'skills': skills}
                return Response(response)

    def post(self, request):
        tracker = request.data
        serializer = TrackerSerializer(data=tracker)
        if serializer.is_valid(raise_exception=True):
            tracker_saved = serializer.save(user_creator=request.user)
        thread = threading.Thread(target=parse_one_tracker, args=[tracker_saved.id])
        thread.start()
        return Response({'success': f'tracker {tracker_saved.search_text} created succesfully. It`s id - {tracker_saved.id}'})

    def put(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            return Response({"error": "Method PUT not allowed"})

        try:
            tracker = JobTracker.objects.get(pk=pk)
        except:
            return Response({"error": "Object does not exists"})
        self.check_object_permissions(self.request, tracker)
        serializer = TrackerSerializer(data=request.data, instance=tracker)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"post": serializer.data})

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            return Response({"error": "Method DELETE not allowed"})

        try:
            tracker = JobTracker.objects.get(pk=pk)
        except:
            return Response({"error": "Object does not exists"})
        self.check_object_permissions(self.request, tracker)
        tracker.delete()
        return Response({"post": f"deleted tracker {pk}"})


class AreaListView(ListAPIView):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    pagination_class = None
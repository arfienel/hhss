from django.urls import path
from.views import *

urlpatterns = [
    path('', index, name='index'),
    path('create_tracker/', create_tracker, name='create_tracker'),
    path('delete_tracker/', delete_tracker, name='delete_tracker'),
    path('update_tracker/', update_tracker, name='update_tracker'),
    path('accounts/registration/', registration, name='registration'),
    path('logout/', user_logout, name='logout'),
    path('load_parser_data/', load_parser_data, name='load_parser_data'),
    path('list_trackers/', list_trackers, name='list_trackers'),
    path('list_more_trackers/', list_more_trackers, name='list_more_trackers')
]

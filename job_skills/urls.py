from django.urls import path
from.views import *

urlpatterns = [
    path('', index, name='index'),
    path('create_tracker/', create_tracker, name='create_tracker'),
    path('delete_tracker/', delete_tracker, name='delete_tracker'),
    path('update_tracker/', update_tracker, name='update_tracker'),
    path('accounts/registration/', registration, name='registration'),
    path('logout/', user_logout, name='logout')
]

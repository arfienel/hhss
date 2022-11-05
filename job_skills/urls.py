from django.urls import include, path
from rest_framework import routers
from.views import *

router = routers.DefaultRouter()

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/job_trackers/', JobTrackerView.as_view(), name='get_tracker'),
    path('api/job_trackers/<int:pk>/', JobTrackerView.as_view(), name='put_tracker'),
    path('api/areas/', AreaListView.as_view(), name='areas'),
    path('', index, name='index'),
    path('create_tracker/', create_tracker, name='create_tracker'),
    path('delete_tracker/', delete_tracker, name='delete_tracker'),
    # path('update_tracker/', update_tracker, name='update_tracker'),
    path('accounts/registration/', registration, name='registration'),
    path('logout/', user_logout, name='logout'),
    path('load_parser_data/', load_parser_data, name='load_parser_data'),
    path('list_trackers/', list_trackers, name='list_trackers'),
    path('list_more_trackers/', list_more_trackers, name='list_more_trackers'),
    path('subscribe_on_tracker/', subscribe_on_tracker, name='subscribe_on_tracker'),
    path('unsubscribe_from_tracker/', unsubscribe_from_tracker, name='unsubscribe_from_tracker'),
]

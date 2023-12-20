# votable_app/urls.py
from django.urls import path
from .views import CreateVotableView, GetAllVotablesView, VoteView, get_current_user, GetSingleVotableView

urlpatterns = [
    path('create_votable/', CreateVotableView.as_view(), name='create_votable'),
    path('get_all_votables/', GetAllVotablesView.as_view(), name='get_all_votables'),
    path('get_votable/<int:votable_id>/', GetSingleVotableView.as_view(), name='get_single_votable'),
    path('vote/<int:votable_id>/', VoteView.as_view(), name='vote'),
    path('current_user/', get_current_user, name='get_current_user'),
]
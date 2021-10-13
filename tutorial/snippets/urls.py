from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from snippets import views

urlpatterns = [
    path('snippets/', views.SnippetList.as_view(), name='snippets-view'),
    path('snippets/<int:pk>/', views.SnippetDetail.as_view(), name='snippets-detail-view'),
    path('users/', views.UserList.as_view(), name='users-view'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='users-detail')
]

urlpatterns = format_suffix_patterns(urlpatterns)
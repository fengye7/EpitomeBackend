from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from kling_server.views import DownloadMediaView, UpdateMediaView,UserImageListView, UserVideoListView

urlpatterns = [  
      path('downloadMedia/', DownloadMediaView.as_view(),  name='download_media'),
      path('updateMedia/', UpdateMediaView.as_view(),  name='update_media'),
      path('userImageList/',UserImageListView.as_view(), name='user_image_list'),
      path('userVideoList/',UserVideoListView.as_view(), name='user_video_list'),
]


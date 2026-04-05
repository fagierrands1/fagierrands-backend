from django.urls import path
from . import views

app_name = 'voice'

urlpatterns = [
    path('transcribe', views.transcribe_audio, name='transcribe'),
    path('process-command', views.process_voice_command, name='process_command'),
    path('context', views.get_voice_context, name='get_context'),
]
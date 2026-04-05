from django.shortcuts import render

def deployment_check_view(request):
    return render(request, 'deployment_check.html')

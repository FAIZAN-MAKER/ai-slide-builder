from django.shortcuts import render

# Create your views here.

def slide_builder(request):
    return render(request, 'slide_builder.html')
from django.shortcuts import render
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"message": "Health check: status ok"}, status=200)

from django.urls import path
from django.http import JsonResponse

def test_users(request):
    return JsonResponse({"message": "Users API working"})

urlpatterns = [
    path("", test_users),
]

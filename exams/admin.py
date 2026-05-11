from django.contrib import admin
from .models import Question, Result, UserResponse

admin.site.register(Question)
admin.site.register(UserResponse)
admin.site.register(Result)

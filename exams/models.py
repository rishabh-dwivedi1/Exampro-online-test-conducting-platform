from django.contrib.auth.models import User
from django.db import models


class Question(models.Model):
    subject = models.CharField(max_length=40, default="Computer Science")
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])
    topic = models.CharField(max_length=80, default="General Aptitude")

    def __str__(self):
        return self.text[:70]


class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="results")
    subject = models.CharField(max_length=40, default="All Subjects")
    title = models.CharField(max_length=120, default="PCM Mock Test")
    total_questions = models.PositiveIntegerField()
    attempted = models.PositiveIntegerField()
    correct = models.PositiveIntegerField()
    incorrect = models.PositiveIntegerField()
    score = models.PositiveIntegerField()
    accuracy = models.FloatField(default=0)
    time_taken = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.score}"


class UserResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name="responses", null=True, blank=True)
    selected_answer = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(default=False)
    marked_for_review = models.BooleanField(default=False)

    class Meta:
        unique_together = ("result", "question")

    def __str__(self):
        return f"{self.user.username} - Q{self.question_id}"

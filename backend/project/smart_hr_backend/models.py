from django.db import models
from django.contrib.auth.models import User

class SmartGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True) 
    goal = models.TextField()
    measure_of_success = models.TextField()
    kpi_metrics = models.TextField()
    outcome_defined = models.CharField(max_length=10)
    quantifiable_objective = models.FloatField()
    skills_available = models.CharField(max_length=10)
    obstacles_considered = models.CharField(max_length=10)
    thrust_area = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    response = models.TextField()
    final_goal = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - Goal: {self.goal[:50]}..."

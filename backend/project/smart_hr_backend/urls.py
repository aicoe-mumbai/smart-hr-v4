from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('submit-goal/', submit_goal, name='submit-goal'),
    path('user-goals/', get_user_goals, name='user-goals'),
    path("user-goals/<int:goal_id>/delete/", delete_smart_goal, name="delete_smart_goal"),
    path("update-goals/<int:goal_id>/", update_smart_goal, name="update-smart-goal"),
    path('final-goal/', final_goal)
]

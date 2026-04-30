# app/serializers.py

from rest_framework import serializers
from .models import (
    SmartGoal,
    GapAnalysisRecord,
)


class SmartGoalSerializer(serializers.ModelSerializer):
    aligned_objectives = serializers.SerializerMethodField()
    thrust_area_codes = serializers.SerializerMethodField()
    group_objective_codes = serializers.SerializerMethodField()

    class Meta:
        model = SmartGoal
        fields = [
            "id",
            "user",
            "goal",
            "measure_of_success",
            "kpi_metrics",
            "outcome_defined",
            "quantifiable_objective",
            "skills_available",
            "obstacles_considered",
            "thrust_area",
            "sub_category",
            "group_objectives",
            "additional_sub_category",
            "user_bu",
            "crosslinked_bus",
            "start_date",
            "end_date",
            "response",
            "final_goal",
            "thrust_area_code",
            "group_objective_code",
            "thrust_area_codes",
            "group_objective_codes",
            "aligned_objectives",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "response", "created_at", "updated_at"]

    def get_aligned_objectives(self, obj):
        # Returns list of dicts from goals.db
        return obj.get_aligned_objectives()

    def get_thrust_area_codes(self, obj):
        return obj.get_ta_codes()

    def get_group_objective_codes(self, obj):
        return obj.get_go_codes()


class GoalAlignmentSerializer(serializers.Serializer):
    goal_id = serializers.IntegerField()
    user_bu = serializers.CharField(allow_null=True, required=False)
    thrust_area = serializers.CharField(allow_null=True, required=False)
    group_objective = serializers.CharField(allow_null=True, required=False)
    crosslinked_bus = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    aligned_objectives = serializers.ListField()


class GapAnalysisRecordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    analysis_date_formatted = serializers.SerializerMethodField()
    goals_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GapAnalysisRecord
        fields = [
            'id',
            'username',
            'analysis_date',
            'analysis_date_formatted',
            'goals_analyzed',
            'goals_count',
            'ta_coverage',
            'go_coverage',
            'analysis_result'
        ]
    
    def get_analysis_date_formatted(self, obj):
        return obj.analysis_date.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_goals_count(self, obj):
        return len(obj.goals_analyzed)

# app/serializers.py

from rest_framework import serializers
from .models import (
    SmartGoal,
    OrgUnit,
    BUObjective,
    BUObjectiveTALink,
    BUObjectiveGOLink,
)


class OrgUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgUnit
        fields = ["id", "code", "name", "sheet_name", "created_at"]


class BUObjectiveTALinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BUObjectiveTALink
        fields = ["id", "ta_code_raw", "ta_code_normalized"]


class BUObjectiveGOLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BUObjectiveGOLink
        fields = ["id", "go_code_raw", "go_code_normalized"]


class BUObjectiveSerializer(serializers.ModelSerializer):
    bu_name = serializers.CharField(source="org_unit.name", read_only=True)
    bu_code = serializers.CharField(source="org_unit.code", read_only=True)
    thrust_area = serializers.SerializerMethodField()
    group_objective = serializers.SerializerMethodField()
    objective_text = serializers.CharField(source="goal_text", read_only=True)
    ta_links = BUObjectiveTALinkSerializer(many=True, read_only=True)
    go_links = BUObjectiveGOLinkSerializer(many=True, read_only=True)

    class Meta:
        model = BUObjective
        fields = [
            "id",
            "bu_name",
            "bu_code",
            "parameter_name",
            "objective_text",
            "goal_text",
            "measure_of_success",
            "thrust_area",
            "group_objective",
            "linkage_ta_raw",
            "linkage_go_raw",
            "source_sheet",
            "source_row_no",
            "remarks",
            "ta_links",
            "go_links",
            "created_at",
            "updated_at",
        ]

    def get_thrust_area(self, obj):
        vals = obj.ta_links.values_list("ta_code_normalized", flat=True).distinct()
        return ", ".join(vals)

    def get_group_objective(self, obj):
        vals = obj.go_links.values_list("go_code_normalized", flat=True).distinct()
        return ", ".join(vals)


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
        qs = obj.get_aligned_objectives()
        return BUObjectiveSerializer(qs, many=True).data

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
    aligned_objectives = BUObjectiveSerializer(many=True)

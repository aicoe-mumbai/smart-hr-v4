from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
import logging
import re

logger = logging.getLogger(__name__)


class OrgUnit(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150, unique=True)
    sheet_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class BUObjective(models.Model):
    org_unit = models.ForeignKey(
        OrgUnit,
        on_delete=models.CASCADE,
        related_name="objectives"
    )
    parameter_name = models.CharField(max_length=255, blank=True, null=True)
    goal_text = models.TextField()
    measure_of_success = models.TextField(blank=True, null=True)
    linkage_ta_raw = models.TextField(blank=True, null=True)
    linkage_go_raw = models.TextField(blank=True, null=True)
    source_sheet = models.CharField(max_length=200)
    source_row_no = models.IntegerField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["org_unit__name", "source_row_no", "id"]

    def __str__(self):
        return f"{self.org_unit.name} - {self.goal_text[:80]}"

    @property
    def bu_name(self):
        return self.org_unit.name

    @property
    def thrust_area(self):
        vals = list(
            self.ta_links.values_list("ta_code_normalized", flat=True).distinct()
        )
        return ", ".join(vals)

    @property
    def group_objective(self):
        vals = list(
            self.go_links.values_list("go_code_normalized", flat=True).distinct()
        )
        return ", ".join(vals)


class BUObjectiveTALink(models.Model):
    objective = models.ForeignKey(
        BUObjective,
        on_delete=models.CASCADE,
        related_name="ta_links"
    )
    ta_code_raw = models.CharField(max_length=100)
    ta_code_normalized = models.CharField(max_length=50, db_index=True)

    class Meta:
        ordering = ["ta_code_normalized"]

    def __str__(self):
        return f"{self.objective_id} -> {self.ta_code_normalized}"


class BUObjectiveGOLink(models.Model):
    objective = models.ForeignKey(
        BUObjective,
        on_delete=models.CASCADE,
        related_name="go_links"
    )
    go_code_raw = models.CharField(max_length=100)
    go_code_normalized = models.CharField(max_length=50, db_index=True)

    class Meta:
        ordering = ["go_code_normalized"]

    def __str__(self):
        return f"{self.objective_id} -> {self.go_code_normalized}"


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
    group_objectives = models.TextField(blank=True, null=True)
    additional_sub_category = models.CharField(max_length=255, blank=True, null=True)

    user_bu = models.CharField(max_length=100, blank=True, null=True)
    crosslinked_bus = models.JSONField(default=list, blank=True, null=True)

    start_date = models.DateField()
    end_date = models.DateField()
    response = models.TextField()
    final_goal = models.TextField(blank=True, null=True)

    # Optional normalized codes for future-safe matching
    thrust_area_code = models.CharField(max_length=50, blank=True, null=True)
    group_objective_code = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        username = self.user.username if self.user else "anonymous"
        return f"{username} - Goal: {self.goal[:50]}..."

    @staticmethod
    def _split_multi_value(raw_value):
        if not raw_value:
            return []
        parts = re.split(r"[,/&]|\band\b", str(raw_value), flags=re.IGNORECASE)
        return [p.strip() for p in parts if p and p.strip()]

    @staticmethod
    def _normalize_ta_code(value):
        if not value:
            return None
        value = str(value).upper().strip()
        value = re.sub(r"\s+", " ", value)

        m = re.search(r"TA\s*[-]?\s*(\d+(?:\.\d+)?)", value)
        if m:
            return f"TA-{m.group(1)}"

        m = re.match(r"^(\d+(?:\.\d+)?)$", value)
        if m:
            return f"TA-{m.group(1)}"

        return None

    @staticmethod
    def _normalize_go_code(value):
        if not value:
            return None

        value = str(value).upper().strip()
        
        # Handle text-based group objectives from frontend
        go_mapping = {
            "ENVIRONMENT, SAFETY, SUSTAINABILITY & GOVERNANCE": "GO-1",
            "ENVIRONMENT SAFETY SUSTAINABILITY AND GOVERNANCE": "GO-1",
            "FINANCIAL PARAMETERS": "GO-2", 
            "OPERATIONAL EXCELLENCE": "GO-3",
            "R&D AND DESIGN": "GO-4",
            "RD AND DESIGN": "GO-4",
            "ORGANISATIONAL EXCELLENCE": "GO-5",
            "CUSTOMER DELIGHT": "GO-6",
            "WORK CULTURE AND EMPLOYEE ENGAGEMENT": "GO-7"
        }
        
        normalized_value = value.replace(",", "").replace("R&D", "RD").replace("&", "AND")
        if normalized_value in go_mapping:
            return go_mapping[normalized_value]
        
        # Handle GO-X format
        value = value.replace(".", "")
        value = re.sub(r"\s+", "", value)
        
        m = re.search(r"GO[-]?(\d+)(?:\(?([A-Z])\)?)?$", value)
        if m:
            num = m.group(1)
            alpha = m.group(2)
            return f"GO-{num}({alpha.lower()})" if alpha else f"GO-{num}"

        m = re.match(r"^(\d+)([A-Z])$", value)
        if m:
            return f"GO-{m.group(1)}({m.group(2).lower()})"

        m = re.match(r"^(\d+)\(([A-Z])\)$", value)
        if m:
            return f"GO-{m.group(1)}({m.group(2).lower()})"

        m = re.match(r"^(\d+)$", value)
        if m:
            return f"GO-{m.group(1)}"

        return None

    def get_ta_codes(self):
        codes = set()

        if self.thrust_area_code:
            for item in self._split_multi_value(self.thrust_area_code):
                norm = self._normalize_ta_code(item)
                if norm:
                    codes.add(norm)

        if not codes and self.thrust_area:
            norm = self._normalize_ta_code(self.thrust_area)
            if norm:
                codes.add(norm)

        if not codes and self.sub_category:
            m = re.match(r"^(\d+(?:\.\d+)?)", self.sub_category.strip())
            if m:
                codes.add(f"TA-{m.group(1)}")

        return sorted(codes)

    def get_go_codes(self):
        codes = set()

        if self.group_objective_code:
            for item in self._split_multi_value(self.group_objective_code):
                norm = self._normalize_go_code(item)
                if norm:
                    codes.add(norm)

        if not codes and self.group_objectives:
            for item in self._split_multi_value(self.group_objectives):
                norm = self._normalize_go_code(item)
                if norm:
                    codes.add(norm)

        return sorted(codes)

    @staticmethod
    def _normalize_bu_name(value):
        """Normalize BU names to match database format"""
        if not value:
            return None
        
        bu_mapping = {
            "QA QC": "QA-QC",
            "MPES- MES": "MPES-MES",
            "MPES- SVP": "MPES-SVP",
            "MPES- SHIPBUILDING": "MPES-SHIPBUILDING"
        }
        
        return bu_mapping.get(value, value)

    def get_bus_to_check(self):
        bus_to_check = []
        if self.user_bu:
            bus_to_check.append(self._normalize_bu_name(self.user_bu))
        if self.crosslinked_bus:
            normalized_crosslinked = [self._normalize_bu_name(bu) for bu in self.crosslinked_bus]
            bus_to_check.extend(normalized_crosslinked)

        cleaned = []
        seen = set()
        for b in bus_to_check:
            if b and b not in seen:
                seen.add(b)
                cleaned.append(b)
        return cleaned

    def get_aligned_objectives(self):
        bus_to_check = self.get_bus_to_check()
        ta_codes = self.get_ta_codes()
        go_codes = self.get_go_codes()

        logger.info("=== ALIGNMENT CALCULATION ===")
        logger.info(f"Goal ID: {self.id}")
        logger.info(f"User BU: {self.user_bu}")
        logger.info(f"Crosslinked BUs: {self.crosslinked_bus}")
        logger.info(f"All BUs to check: {bus_to_check}")
        logger.info(f"TA Codes: {ta_codes}")
        logger.info(f"GO Codes: {go_codes}")

        qs = BUObjective.objects.select_related("org_unit").prefetch_related(
            "ta_links", "go_links"
        )

        if bus_to_check:
            qs = qs.filter(
                Q(org_unit__name__in=bus_to_check) |
                Q(org_unit__code__in=bus_to_check)
            )
        else:
            return BUObjective.objects.none()

        if ta_codes and go_codes:
            qs = qs.filter(
                ta_links__ta_code_normalized__in=ta_codes,
                go_links__go_code_normalized__in=go_codes
            )
        elif ta_codes:
            qs = qs.filter(ta_links__ta_code_normalized__in=ta_codes)
        elif go_codes:
            qs = qs.filter(go_links__go_code_normalized__in=go_codes)
        else:
            return BUObjective.objects.none()

        aligned_objs = qs.distinct()

        logger.info(f"Found {aligned_objs.count()} aligned objectives:")
        for obj in aligned_objs:
            logger.info(f"  - BU: {obj.org_unit.name}")
            logger.info(f"    TA: {obj.thrust_area}")
            logger.info(f"    GO: {obj.group_objective}")
            logger.info(f"    Objective Text: {obj.goal_text}")
            logger.info("    ---")
        logger.info("=== END ALIGNMENT ===")

        return aligned_objs

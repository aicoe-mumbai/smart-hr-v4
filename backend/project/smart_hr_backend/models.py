from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
import logging
import re
from .goals_db_utils import get_bu_objectives, get_all_ta_codes, get_all_go_codes

logger = logging.getLogger(__name__)


class GapAnalysisRecord(models.Model):
    """Track gap analysis completion for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gap_analyses')
    analysis_date = models.DateTimeField(auto_now_add=True)
    goals_analyzed = models.JSONField(default=list)  # List of goal IDs
    ta_coverage = models.FloatField()
    go_coverage = models.FloatField()
    analysis_result = models.JSONField()  # Store full analysis result
    
    class Meta:
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"{self.user.username} - Gap Analysis on {self.analysis_date.strftime('%Y-%m-%d')}"



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
            "ENVIRONMENT, SAFETY, SUSTAINABILITY AND GOVERNANCE": "GO-1",
            "FINANCIAL PARAMETERS": "GO-2", 
            "OPERATIONAL EXCELLENCE": "GO-3",
            "TECHNOLOGY & INNOVATION": "GO-4",
            "TECHNOLOGY AND INNOVATION": "GO-4",
            "R&D AND DESIGN": "GO-4",
            "RD AND DESIGN": "GO-4",
            "ORGANISATIONAL EXCELLENCE": "GO-5",
            "ORGANIZATIONAL EXCELLENCE": "GO-5",
            "CUSTOMER DELIGHT": "GO-6",
            "WORK CULTURE AND EMPLOYEE ENGAGEMENT": "GO-7"
        }
        
        # Try direct mapping first
        if value in go_mapping:
            return go_mapping[value]
        
        # Try normalized version (remove commas and replace & with AND)
        normalized_value = value.replace(",", "").replace("&", "AND").strip()
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

        logger.info(f"Extracting GO codes from goal...")
        logger.info(f"  group_objective_code field: {self.group_objective_code}")
        logger.info(f"  group_objectives field: {self.group_objectives}")

        if self.group_objective_code:
            for item in self._split_multi_value(self.group_objective_code):
                norm = self._normalize_go_code(item)
                if norm:
                    codes.add(norm)
                    logger.info(f"  Normalized '{item}' -> '{norm}'")

        if not codes and self.group_objectives:
            # Don't split group_objectives - it's a single value!
            # The field contains the full GO name like "Environment, Safety, Sustainability & Governance"
            logger.info(f"  Attempting to normalize full GO value: '{self.group_objectives}'")
            norm = self._normalize_go_code(self.group_objectives)
            if norm:
                codes.add(norm)
                logger.info(f"  Successfully normalized '{self.group_objectives}' -> '{norm}'")
            else:
                logger.warning(f"  Failed to normalize: '{self.group_objectives}'")

        logger.info(f"  Final GO codes extracted: {sorted(codes)}")
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
        """Get list of BUs to check for alignment - ONLY cross-linked BUs, NOT user's own BU"""
        bus_to_check = []
        # ONLY include cross-linked BUs, NOT user's own BU
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
        """
        Get aligned objectives from goals.db based on user's BU, TA, and GO selections
        Returns list of objective dicts from goals.db
        """
        bus_to_check = self.get_bus_to_check()
        ta_codes = self.get_ta_codes()
        go_codes = self.get_go_codes()

        logger.info("=== ALIGNMENT CALCULATION (using goals.db) ===")
        logger.info(f"Goal ID: {self.id}")
        logger.info(f"User BU: {self.user_bu}")
        logger.info(f"Crosslinked BUs: {self.crosslinked_bus}")
        logger.info(f"All BUs to check: {bus_to_check}")
        logger.info(f"TA Codes: {ta_codes}")
        logger.info(f"GO Codes: {go_codes}")

        if not bus_to_check:
            logger.warning("No BUs to check!")
            return []

        # Query goals.db for aligned objectives
        # Require BOTH TA and GO match for strict alignment
        if ta_codes and go_codes:
            logger.info(f"Filtering with BOTH TA ({ta_codes}) AND GO ({go_codes})")
            aligned_objs = get_bu_objectives(bus_to_check, ta_codes=ta_codes, go_codes=go_codes)
        elif ta_codes:
            logger.warning(f"GO codes not found! Filtering by TA only: {ta_codes}")
            aligned_objs = get_bu_objectives(bus_to_check, ta_codes=ta_codes)
        elif go_codes:
            logger.warning(f"TA codes not found! Filtering by GO only: {go_codes}")
            aligned_objs = get_bu_objectives(bus_to_check, go_codes=go_codes)
        else:
            logger.error("Neither TA nor GO codes found! Cannot filter objectives.")
            return []

        logger.info(f"Found {len(aligned_objs)} aligned objectives:")
        for obj in aligned_objs:
            logger.info(f"  - BU: {obj['bu_name']}")
            logger.info(f"    TA: {obj['thrust_area_str']}")
            logger.info(f"    GO: {obj['group_objective_str']}")
            logger.info(f"    Objective Text: {obj['goal_text'][:100]}...")
            logger.info("    ---")
        logger.info("=== END ALIGNMENT ===")

        return aligned_objs

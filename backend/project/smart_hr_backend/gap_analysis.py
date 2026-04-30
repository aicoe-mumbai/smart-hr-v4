import logging
from collections import defaultdict
from .models import SmartGoal, GapAnalysisRecord
from .goals_db_utils import get_thrust_areas, get_group_objectives, get_bu_objectives
from django.conf import settings
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import json
import re

logger = logging.getLogger(__name__)

def analyze_goal_coverage(selected_goal_ids, user):
    """
    Analyze coverage of company GO/TA by selected user goals
    Returns gaps and coverage statistics
    """
    logger.info(f"=== GAP ANALYSIS FOR USER: {user.username} ===")
    logger.info(f"Analyzing {len(selected_goal_ids)} selected goals")
    
    # Fetch selected goals
    selected_goals = SmartGoal.objects.filter(id__in=selected_goal_ids, user=user)
    
    if not selected_goals.exists():
        return {
            'error': 'No goals found',
            'total_goals_analyzed': 0
        }
    
    # Get all company TAs and GOs from goals.db
    all_tas = get_thrust_areas()
    all_gos = get_group_objectives()
    
    # Extract unique main TA codes (TA-1, TA-2, etc.)
    all_ta_codes = set()
    for ta in all_tas:
        # Extract main code (TA-1, TA-2, etc.)
        match = re.match(r'(TA-\d+)', ta['code'])
        if match:
            all_ta_codes.add(match.group(1))
    
    # Get main GO codes (already in GO-1, GO-2 format from goals_db_utils)
    all_go_codes = set(go['code'] for go in all_gos)
    
    # Track coverage
    covered_tas = set()
    covered_gos = set()
    ta_goal_mapping = defaultdict(list)
    go_goal_mapping = defaultdict(list)
    
    # Analyze each goal
    goal_details = []
    for goal in selected_goals:
        ta_codes = goal.get_ta_codes()
        go_codes = goal.get_go_codes()
        
        covered_tas.update(ta_codes)
        covered_gos.update(go_codes)
        
        for ta in ta_codes:
            ta_goal_mapping[ta].append({
                'goal_id': goal.id,
                'goal_text': goal.goal[:100]
            })
        
        for go in go_codes:
            go_goal_mapping[go].append({
                'goal_id': goal.id,
                'goal_text': goal.goal[:100]
            })
        
        goal_details.append({
            'id': goal.id,
            'goal': goal.goal,
            'user_bu': goal.user_bu,
            'crosslinked_bus': goal.crosslinked_bus or [],
            'thrust_areas': ta_codes,
            'group_objectives': go_codes,
            'start_date': str(goal.start_date),
            'end_date': str(goal.end_date)
        })
    
    # Identify gaps
    missing_tas = all_ta_codes - covered_tas
    missing_gos = all_go_codes - covered_gos
    
    # Get details for missing items
    missing_ta_details = []
    for ta_code in missing_tas:
        # Find TA with this code
        ta = next((t for t in all_tas if t['code'] == ta_code), None)
        if ta:
            missing_ta_details.append({
                'code': ta['code'],
                'description': ta['description']
            })
    
    missing_go_details = []
    for go_code in missing_gos:
        # Find GO with this code
        go = next((g for g in all_gos if g['code'] == go_code), None)
        if go:
            missing_go_details.append({
                'code': go['code'],
                'description': go['description'],
                'parameter': go.get('parameter', 'N/A')
            })
    
    # Calculate coverage percentages
    ta_coverage = (len(covered_tas) / len(all_ta_codes) * 100) if all_ta_codes else 0
    go_coverage = (len(covered_gos) / len(all_go_codes) * 100) if all_go_codes else 0
    
    # Get BU objectives for covered areas
    bu_objectives_coverage = analyze_bu_objectives_coverage(selected_goals)
    
    # LLM Analysis
    llm_insights = generate_llm_insights(
        goal_details, 
        missing_ta_details, 
        missing_go_details,
        ta_coverage,
        go_coverage
    )
    
    logger.info(f"TA Coverage: {ta_coverage:.2f}% ({len(covered_tas)}/{len(all_ta_codes)})")
    logger.info(f"GO Coverage: {go_coverage:.2f}% ({len(covered_gos)}/{len(all_go_codes)})")
    logger.info(f"Missing TAs: {missing_tas}")
    logger.info(f"Missing GOs: {missing_gos}")
    
    return {
        'total_goals_analyzed': len(selected_goals),
        'goal_details': goal_details,
        'coverage': {
            'thrust_areas': {
                'total': len(all_ta_codes),
                'covered': len(covered_tas),
                'coverage_percentage': round(ta_coverage, 2),
                'covered_list': sorted(list(covered_tas)),
                'missing_list': sorted(list(missing_tas)),
                'missing_details': missing_ta_details,
                'ta_to_goals': dict(ta_goal_mapping)
            },
            'group_objectives': {
                'total': len(all_go_codes),
                'covered': len(covered_gos),
                'coverage_percentage': round(go_coverage, 2),
                'covered_list': sorted(list(covered_gos)),
                'missing_list': sorted(list(missing_gos)),
                'missing_details': missing_go_details,
                'go_to_goals': dict(go_goal_mapping)
            }
        },
        'bu_objectives_analysis': bu_objectives_coverage,
        'llm_insights': llm_insights
    }

def analyze_bu_objectives_coverage(selected_goals):
    """
    Analyze how well selected goals align with BU objectives from goals.db
    """
    bu_coverage = defaultdict(lambda: {
        'total_objectives': 0,
        'aligned_objectives': 0,
        'alignment_percentage': 0,
        'aligned_details': []
    })
    
    for goal in selected_goals:
        aligned_objs = goal.get_aligned_objectives()  # Returns list of dicts from goals.db
        
        for obj in aligned_objs:
            bu_name = obj['bu_name']
            bu_coverage[bu_name]['aligned_objectives'] += 1
            bu_coverage[bu_name]['aligned_details'].append({
                'objective_id': obj['id'],
                'objective_text': obj['goal_text'][:100],
                'thrust_area': obj['thrust_area_str'],
                'group_objective': obj['group_objective_str'],
                'goal_id': goal.id,
                'goal_text': goal.goal[:100]
            })
    
    # Get total objectives per BU from goals.db
    for bu_name in bu_coverage.keys():
        # Query goals.db for total count
        all_objs = get_bu_objectives([bu_name])
        total = len(all_objs)
        bu_coverage[bu_name]['total_objectives'] = total
        if total > 0:
            bu_coverage[bu_name]['alignment_percentage'] = round(
                (bu_coverage[bu_name]['aligned_objectives'] / total) * 100, 2
            )
    
    return dict(bu_coverage)

def generate_llm_insights(goal_details, missing_ta_details, missing_go_details, ta_coverage, go_coverage):
    """Use LLM to generate strategic insights about goal coverage and gaps"""
    logger.info("=== GENERATING LLM INSIGHTS ===")
    
    try:
        client = ChatCompletionsClient(
            endpoint=settings.OPENAI_ENDPOINT,
            credential=AzureKeyCredential(settings.OPENAI_API_KEY)
        )
        
        goals_summary = "\n".join([
            f"Goal {i+1}: {goal['goal'][:200]}... (TA: {', '.join(goal['thrust_areas'])}, GO: {', '.join(goal['group_objectives'])})"
            for i, goal in enumerate(goal_details)
        ])
        
        missing_tas_summary = "\n".join([
            f"- {ta['code']}: {ta['description'][:150]}..."
            for ta in missing_ta_details
        ]) if missing_ta_details else "None - All Thrust Areas covered!"
        
        missing_gos_summary = "\n".join([
            f"- {go['code']}: {go['description'][:150]}..."
            for go in missing_go_details
        ]) if missing_go_details else "None - All Group Objectives covered!"
        
        prompt = f"""You are a strategic business analyst reviewing a BU leader's goal portfolio.

GOALS SUBMITTED ({len(goal_details)} total):
{goals_summary}

COVERAGE ANALYSIS:
- Thrust Area Coverage: {ta_coverage:.1f}%
- Group Objective Coverage: {go_coverage:.1f}%

MISSING THRUST AREAS:
{missing_tas_summary}

MISSING GROUP OBJECTIVES:
{missing_gos_summary}

Provide a strategic analysis in JSON format:
{{
    "overall_assessment": "Brief 2-3 sentence assessment",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "critical_gaps": ["gap 1", "gap 2", "gap 3"],
    "strategic_recommendations": [
        {{
            "priority": "High/Medium/Low",
            "area": "TA or GO code",
            "recommendation": "Specific actionable recommendation",
            "rationale": "Why this is important"
        }}
    ],
    "balance_analysis": "Analysis of balance across strategic areas",
    "risk_assessment": "Potential risks from identified gaps"
}}

Return ONLY valid JSON, no markdown."""
        
        logger.info("Calling Azure OpenAI for strategic insights...")
        
        response = client.complete(
            messages=[
                SystemMessage(content="You are a strategic business analyst. Always return valid JSON."),
                UserMessage(content=prompt)
            ],
            model=settings.OPENAI_MODEL_NAME,
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = ""
        if hasattr(response, 'choices') and response.choices:
            if hasattr(response.choices[0], 'message') and response.choices[0].message:
                response_text = response.choices[0].message.content or ""
        
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        insights = json.loads(response_text)
        logger.info("✅ LLM insights generated successfully")
        return insights
        
    except Exception as e:
        logger.error(f"❌ Failed to generate LLM insights: {str(e)}")
        return {
            "overall_assessment": f"Analysis of {len(goal_details)} goals shows {ta_coverage:.1f}% TA coverage and {go_coverage:.1f}% GO coverage.",
            "strengths": [
                "Goals have been submitted and are being tracked",
                f"Covering {len(goal_details)} strategic objectives"
            ],
            "critical_gaps": [
                f"{len(missing_ta_details)} Thrust Areas not covered" if missing_ta_details else "All Thrust Areas covered",
                f"{len(missing_go_details)} Group Objectives not covered" if missing_go_details else "All Group Objectives covered"
            ],
            "strategic_recommendations": [],
            "balance_analysis": "Unable to generate detailed analysis. Please review missing areas manually.",
            "risk_assessment": "LLM analysis unavailable. Manual review recommended.",
            "error": str(e)
        }

def get_recommendations(gap_analysis_result):
    """
    Generate recommendations based on gap analysis
    """
    recommendations = []
    
    ta_coverage = gap_analysis_result['coverage']['thrust_areas']
    go_coverage = gap_analysis_result['coverage']['group_objectives']
    
    # TA recommendations
    if ta_coverage['coverage_percentage'] < 100:
        recommendations.append({
            'type': 'thrust_area_gap',
            'severity': 'high' if ta_coverage['coverage_percentage'] < 50 else 'medium',
            'message': f"Only {ta_coverage['coverage_percentage']}% of Thrust Areas are covered by your goals.",
            'missing_items': ta_coverage['missing_details'],
            'action': 'Consider setting goals that address the missing Thrust Areas.'
        })
    
    # GO recommendations
    if go_coverage['coverage_percentage'] < 100:
        recommendations.append({
            'type': 'group_objective_gap',
            'severity': 'high' if go_coverage['coverage_percentage'] < 50 else 'medium',
            'message': f"Only {go_coverage['coverage_percentage']}% of Group Objectives are covered by your goals.",
            'missing_items': go_coverage['missing_details'],
            'action': 'Consider setting goals that address the missing Group Objectives.'
        })
    
    # BU alignment recommendations
    bu_analysis = gap_analysis_result.get('bu_objectives_analysis', {})
    for bu_name, data in bu_analysis.items():
        if data['alignment_percentage'] < 50:
            recommendations.append({
                'type': 'bu_alignment_low',
                'severity': 'medium',
                'message': f"Low alignment with {bu_name} objectives ({data['alignment_percentage']}%)",
                'action': f"Review {bu_name} objectives and align your goals accordingly."
            })
    
    if not recommendations:
        recommendations.append({
            'type': 'complete_coverage',
            'severity': 'success',
            'message': 'Excellent! Your goals cover all company Thrust Areas and Group Objectives.',
            'action': 'Continue monitoring and updating your goals as needed.'
        })
    
    return recommendations

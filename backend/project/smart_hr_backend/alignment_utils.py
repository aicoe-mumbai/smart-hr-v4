import logging
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

def calculate_text_similarity(text1, text2):
    """Calculate similarity percentage between two texts"""
    if not text1 or not text2:
        return 0.0
    
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    similarity = SequenceMatcher(None, text1, text2).ratio()
    return round(similarity * 100, 2)

def calculate_alignment_percentage(user_goal, bu_objectives):
    """
    Calculate alignment percentage between user goal and BU objectives
    Returns detailed alignment information with logging
    """
    logger.info("\n" + "="*80)
    logger.info("=== ALIGNMENT PERCENTAGE CALCULATION ===")
    logger.info("="*80)
    
    if not bu_objectives:
        logger.info("No BU objectives found for alignment calculation")
        return {
            'overall_alignment': 0.0,
            'matched_objectives': [],
            'total_objectives': 0
        }
    
    logger.info(f"\nUser Goal Text: {user_goal[:200]}...")
    logger.info(f"\nTotal BU Objectives to compare: {len(bu_objectives)}")
    
    alignments = []
    
    for idx, obj in enumerate(bu_objectives, 1):
        logger.info(f"\n--- Comparing with BU Objective #{idx} ---")
        logger.info(f"BU: {obj.org_unit.name}")
        logger.info(f"TA: {obj.thrust_area}")
        logger.info(f"GO: {obj.group_objective}")
        logger.info(f"Objective Text: {obj.goal_text[:200]}...")
        
        similarity = calculate_text_similarity(user_goal, obj.goal_text)
        
        logger.info(f"Similarity Score: {similarity}%")
        
        alignments.append({
            'bu_objective_id': obj.id,
            'bu_name': obj.org_unit.name,
            'thrust_area': obj.thrust_area,
            'group_objective': obj.group_objective,
            'objective_text': obj.goal_text,
            'similarity_percentage': similarity
        })
    
    # Calculate overall alignment (average of all similarities)
    overall_alignment = sum(a['similarity_percentage'] for a in alignments) / len(alignments)
    
    # Sort by similarity
    alignments.sort(key=lambda x: x['similarity_percentage'], reverse=True)
    
    logger.info("\n" + "="*80)
    logger.info(f"OVERALL ALIGNMENT PERCENTAGE: {overall_alignment:.2f}%")
    logger.info("="*80)
    logger.info("\nTop Matches:")
    for i, match in enumerate(alignments[:3], 1):
        logger.info(f"{i}. {match['bu_name']} - {match['similarity_percentage']}%")
    logger.info("="*80 + "\n")
    
    return {
        'overall_alignment': round(overall_alignment, 2),
        'matched_objectives': alignments,
        'total_objectives': len(bu_objectives)
    }

def log_goal_submission(goal_data):
    """Log detailed information about goal submission"""
    logger.info("\n" + "="*80)
    logger.info("=== GOAL SUBMISSION ===")
    logger.info("="*80)
    logger.info(f"Goal: {goal_data.get('goal', '')[:200]}...")
    logger.info(f"Measure of Success: {goal_data.get('measure_of_success', '')[:200]}...")
    logger.info(f"KPI Metrics: {goal_data.get('kpi_metrics', '')}")
    logger.info(f"Outcome Defined: {goal_data.get('outcome_defined', '')}")
    logger.info(f"Quantifiable Objective: {goal_data.get('quantifiable_objective', '')}")
    logger.info(f"Skills Available: {goal_data.get('skills_available', '')}")
    logger.info(f"Obstacles Considered: {goal_data.get('obstacles_considered', '')}")
    logger.info(f"Thrust Area: {goal_data.get('thrust_area', '')}")
    logger.info(f"Sub Category: {goal_data.get('sub_category', '')}")
    logger.info(f"Group Objectives: {goal_data.get('group_objectives', '')}")
    logger.info(f"User BU: {goal_data.get('user_bu', '')}")
    logger.info(f"Crosslinked BUs: {goal_data.get('crosslinked_bus', [])}")
    logger.info(f"Start Date: {goal_data.get('start_date', '')}")
    logger.info(f"End Date: {goal_data.get('end_date', '')}")
    logger.info("="*80 + "\n")

def log_alignment_search(ta_codes, go_codes, bus_to_check):
    """Log the alignment search parameters"""
    logger.info("\n" + "="*80)
    logger.info("=== ALIGNMENT SEARCH PARAMETERS ===")
    logger.info("="*80)
    logger.info(f"Searching for TA Codes: {ta_codes}")
    logger.info(f"Searching for GO Codes: {go_codes}")
    logger.info(f"In BUs: {buses_to_check}")
    logger.info("="*80 + "\n")

def log_alignment_results(aligned_objectives):
    """Log the results of alignment search"""
    logger.info("\n" + "="*80)
    logger.info("=== ALIGNMENT SEARCH RESULTS ===")
    logger.info("="*80)
    logger.info(f"Total Aligned Objectives Found: {aligned_objectives.count()}")
    
    if aligned_objectives.exists():
        logger.info("\nMatched Objectives:")
        for idx, obj in enumerate(aligned_objectives, 1):
            logger.info(f"\n{idx}. BU: {obj.org_unit.name}")
            logger.info(f"   Parameter: {obj.parameter_name}")
            logger.info(f"   TA: {obj.thrust_area}")
            logger.info(f"   GO: {obj.group_objective}")
            logger.info(f"   Objective: {obj.goal_text[:150]}...")
            logger.info(f"   Source: {obj.source_sheet}, Row {obj.source_row_no}")
    else:
        logger.info("\nNo matching objectives found!")
        logger.info("This could mean:")
        logger.info("  1. No objectives exist for the selected BU(s)")
        logger.info("  2. TA/GO codes don't match any objectives")
        logger.info("  3. Data hasn't been loaded into the database")
    
    logger.info("="*80 + "\n")

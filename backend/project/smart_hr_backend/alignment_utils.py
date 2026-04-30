import logging
import re
import json
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

def calculate_text_similarity(text1, text2):
    """Calculate similarity percentage between two texts using SequenceMatcher"""
    if not text1 or not text2:
        return 0.0
    
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    similarity = SequenceMatcher(None, text1, text2).ratio()
    return round(similarity * 100, 2)

def calculate_alignment_with_llm(user_goal_data, bu_objectives, azure_client, model_name):
    """
    Use Azure OpenAI LLM to calculate semantic alignment between user goal and BU objectives
    Returns detailed alignment information with reasoning
    
    Args:
        user_goal_data: Dict with user's goal information
        bu_objectives: List of dicts from goals.db (not Django ORM objects)
        azure_client: Azure OpenAI client
        model_name: Model name to use
    """
    logger.info("\n" + "="*80)
    logger.info("=== LLM-BASED ALIGNMENT CALCULATION ===")
    logger.info("="*80)
    
    if not bu_objectives:
        logger.info("No BU objectives found for alignment calculation")
        return {
            'overall_alignment': 0.0,
            'matched_objectives': [],
            'matched_by_bu': {},
            'total_objectives': 0
        }
    
    # Format BU objectives for LLM (ONLY goal text, exclude MoS)
    objectives_text = ""
    for idx, obj in enumerate(bu_objectives, 1):
        objectives_text += f"\n--- Objective #{idx} ---\n"
        objectives_text += f"BU: {obj['bu_name']}\n"
        objectives_text += f"TA: {obj['thrust_area_str']}\n"
        objectives_text += f"GO: {obj['group_objective_str']}\n"
        objectives_text += f"Goal: {obj['goal_text']}\n"
    
    # Create prompt for LLM (only use goal text for alignment, not MoS)
    prompt = f"""You are an expert at analyzing organizational goal alignment.

USER'S GOAL:
{user_goal_data.get('goal', '')}

BUSINESS UNIT OBJECTIVES TO COMPARE:
{objectives_text}

TASK:
For each BU objective above, calculate an alignment score (0-100%) based on:
1. Semantic similarity of goal text (consider synonyms, intent, outcomes)
2. Shared themes, technologies, and business outcomes
3. Alignment of targets and timelines

IMPORTANT:
- If a BU objective has multiple numbered points, compare the user's goal with EACH point separately
- Return the HIGHEST alignment score among all points in that objective
- Consider semantic meaning, not just exact text matching
- "Deploy" and "Implement" should be considered similar
- "IoT" and "Industrial IoT" should be considered similar

Return ONLY valid JSON in this EXACT format (no markdown, no code blocks):
{{
    "alignments": [
        {{
            "objective_number": 1,
            "bu_name": "IT & Digital",
            "alignment_score": 95,
            "reasoning": "Nearly identical goals focusing on Industrial IoT deployment",
            "key_overlaps": ["IoT deployment", "real-time visibility", "productivity improvements"]
        }}
    ]
}}
"""
    
    logger.info(f"Sending {len(bu_objectives)} objectives to LLM for alignment analysis...")
    
    try:
        from azure.ai.inference.models import SystemMessage, UserMessage
        
        logger.info("Calling Azure OpenAI API...")
        response = azure_client.complete(
            messages=[
                SystemMessage(content="You are an expert at analyzing organizational goal alignment. Always return valid JSON."),
                UserMessage(content=prompt)
            ],
            model=model_name,
            temperature=0.3,  # Lower temperature for more consistent scoring
            max_tokens=2000
        )
        
        # Extract response text - Azure returns non-streaming response
        response_text = ""
        if hasattr(response, 'choices') and response.choices:
            if hasattr(response.choices[0], 'message') and response.choices[0].message:
                response_text = response.choices[0].message.content or ""
        
        logger.info(f"LLM Response received: {len(response_text)} characters")
        
        # Parse JSON response
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        llm_result = json.loads(response_text)
        
        # Process LLM results into our format
        alignments = []
        bu_grouped = {}
        
        for idx, llm_alignment in enumerate(llm_result.get('alignments', [])):
            obj = bu_objectives[llm_alignment['objective_number'] - 1]
            bu_name = obj['bu_name']
            
            match_data = {
                'bu_objective_id': obj['id'],
                'bu_name': bu_name,
                'thrust_area': obj['thrust_area_str'],
                'group_objective': obj['group_objective_str'],
                'objective_text': obj['goal_text'],
                'parameter_name': obj.get('parameter') or 'Not specified',
                'similarity_percentage': llm_alignment['alignment_score'],
                'reasoning': llm_alignment.get('reasoning', ''),
                'key_overlaps': llm_alignment.get('key_overlaps', []),
                'source_sheet': obj.get('bu_table', 'goals.db'),
                'source_row': obj.get('id', '')
            }
            
            alignments.append(match_data)
            
            if bu_name not in bu_grouped:
                bu_grouped[bu_name] = []
            bu_grouped[bu_name].append(match_data)
            
            logger.info(f"\nObjective #{llm_alignment['objective_number']}: {bu_name}")
            logger.info(f"  Alignment Score: {llm_alignment['alignment_score']}%")
            logger.info(f"  Reasoning: {llm_alignment.get('reasoning', 'N/A')}")
        
        # Calculate overall alignment
        overall_alignment = sum(a['similarity_percentage'] for a in alignments) / len(alignments)
        
        # Sort by similarity
        alignments.sort(key=lambda x: x['similarity_percentage'], reverse=True)
        
        # Calculate per-BU alignment percentages
        bu_alignment_percentages = {}
        for bu_name, matches in bu_grouped.items():
            avg_similarity = sum(m['similarity_percentage'] for m in matches) / len(matches)
            bu_alignment_percentages[bu_name] = round(avg_similarity, 2)
            bu_grouped[bu_name] = sorted(matches, key=lambda x: x['similarity_percentage'], reverse=True)
        
        logger.info("\n" + "="*80)
        logger.info(f"LLM OVERALL ALIGNMENT PERCENTAGE: {overall_alignment:.2f}%")
        logger.info("="*80)
        
        return {
            'overall_alignment': round(overall_alignment, 2),
            'matched_objectives': alignments,
            'matched_by_bu': bu_grouped,
            'bu_alignment_percentages': bu_alignment_percentages,
            'total_objectives': len(bu_objectives),
            'method': 'llm'
        }
        
    except Exception as e:
        logger.error(f"LLM alignment calculation failed: {str(e)}")
        logger.info("Falling back to SequenceMatcher...")
        # Fallback to original method
        return calculate_alignment_percentage(user_goal_data.get('goal', ''), bu_objectives)

def calculate_alignment_percentage(user_goal, bu_objectives):
    """
    Calculate alignment percentage between user goal and BU objectives
    Returns detailed alignment information with logging
    
    Args:
        user_goal: String with user's goal text
        bu_objectives: List of dicts from goals.db (not Django ORM objects)
    """
    logger.info("\n" + "="*80)
    logger.info("=== ALIGNMENT PERCENTAGE CALCULATION ===")
    logger.info("="*80)
    
    if not bu_objectives:
        logger.info("No BU objectives found for alignment calculation")
        return {
            'overall_alignment': 0.0,
            'matched_objectives': [],
            'matched_by_bu': {},
            'total_objectives': 0
        }
    
    logger.info(f"\nUser Goal Text: {user_goal[:200]}...")
    logger.info(f"\nTotal BU Objectives to compare: {len(bu_objectives)}")
    
    alignments = []
    bu_grouped = {}  # Group by BU for better organization
    
    for idx, obj in enumerate(bu_objectives, 1):
        bu_name = obj['bu_name']
        logger.info(f"\n--- Comparing with BU Objective #{idx} ---")
        logger.info(f"BU: {bu_name}")
        logger.info(f"TA: {obj['thrust_area_str']}")
        logger.info(f"GO: {obj['group_objective_str']}")
        logger.info(f"Objective Text: {obj['goal_text'][:200]}...")
        
        similarity = calculate_text_similarity(user_goal, obj['goal_text'])
        
        logger.info(f"Similarity Score: {similarity}%")
        
        match_data = {
            'bu_objective_id': obj['id'],
            'bu_name': bu_name,
            'thrust_area': obj['thrust_area_str'],
            'group_objective': obj['group_objective_str'],
            'objective_text': obj['goal_text'],
            'parameter_name': obj.get('parameter') or 'Not specified',
            'similarity_percentage': similarity,
            'source_sheet': obj.get('bu_table', 'goals.db'),
            'source_row': obj.get('id', '')
        }
        
        alignments.append(match_data)
        
        # Group by BU
        if bu_name not in bu_grouped:
            bu_grouped[bu_name] = []
        bu_grouped[bu_name].append(match_data)
    
    # Calculate overall alignment (average of all similarities)
    overall_alignment = sum(a['similarity_percentage'] for a in alignments) / len(alignments)
    
    # Sort by similarity
    alignments.sort(key=lambda x: x['similarity_percentage'], reverse=True)
    
    # Calculate per-BU alignment percentages
    bu_alignment_percentages = {}
    for bu_name, matches in bu_grouped.items():
        avg_similarity = sum(m['similarity_percentage'] for m in matches) / len(matches)
        bu_alignment_percentages[bu_name] = round(avg_similarity, 2)
        # Sort matches within each BU
        bu_grouped[bu_name] = sorted(matches, key=lambda x: x['similarity_percentage'], reverse=True)
    
    logger.info("\n" + "="*80)
    logger.info(f"OVERALL ALIGNMENT PERCENTAGE: {overall_alignment:.2f}%")
    logger.info("="*80)
    logger.info("\n=== ALIGNMENT BY BUSINESS UNIT ===")
    for bu_name, percentage in sorted(bu_alignment_percentages.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"\n{bu_name}: {percentage}%")
        logger.info(f"  Matched Objectives: {len(bu_grouped[bu_name])}")
        logger.info("  Top 3 Matches:")
        for i, match in enumerate(bu_grouped[bu_name][:3], 1):
            logger.info(f"    {i}. [{match['similarity_percentage']}%] {match['objective_text'][:80]}...")
            logger.info(f"       TA: {match['thrust_area']}, GO: {match['group_objective']}")
    logger.info("\n" + "="*80)
    logger.info("\nTop 5 Overall Matches (Across All BUs):")
    for i, match in enumerate(alignments[:5], 1):
        logger.info(f"{i}. [{match['similarity_percentage']}%] {match['bu_name']}")
        logger.info(f"   {match['objective_text'][:100]}...")
    logger.info("="*80 + "\n")
    
    return {
        'overall_alignment': round(overall_alignment, 2),
        'matched_objectives': alignments,
        'matched_by_bu': bu_grouped,
        'bu_alignment_percentages': bu_alignment_percentages,
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
    logger.info(f"Total Aligned Objectives Found: {len(aligned_objectives)}")
    
    if aligned_objectives:
        logger.info("\nMatched Objectives:")
        for idx, obj in enumerate(aligned_objectives, 1):
            logger.info(f"\n{idx}. BU: {obj['bu_name']}")
            logger.info(f"   Parameter: {obj.get('parameter', 'N/A')}")
            logger.info(f"   TA: {obj['thrust_area_str']}")
            logger.info(f"   GO: {obj['group_objective_str']}")
            logger.info(f"   Objective: {obj['goal_text'][:150]}...")
    else:
        logger.info("\nNo matching objectives found!")
        logger.info("This could mean:")
        logger.info("  1. No objectives exist for the selected BU(s)")
        logger.info("  2. TA/GO codes don't match any objectives")
        logger.info("  3. Data hasn't been loaded into the database")
    
    logger.info("="*80 + "\n")

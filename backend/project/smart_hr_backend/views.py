from rest_framework.response import Response
from django.http import StreamingHttpResponse
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import datetime
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
from .models import SmartGoal, BUObjective
from .serializers import SmartGoalSerializer, BUObjectiveSerializer, GoalAlignmentSerializer
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import logging
import time, base64
from .alignment_utils import (
    calculate_alignment_percentage,
    calculate_alignment_with_llm,
    log_goal_submission,
    log_alignment_search,
    log_alignment_results
)

logger = logging.getLogger(__name__)

def log_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"Endpoint {func.__name__} took {execution_time:.2f} seconds to execute")
        return result
    return wrapper


def user_exists(username):
    User = get_user_model()
    return User.objects.filter(username=username).exists()


def decode_username(encoded_username):
    """Decodes a Base64-encoded username."""
    try:
        return base64.b64decode(encoded_username).decode("utf-8")
    except Exception:
        return None  # Return None if decoding fails
    
@api_view(["POST"])
def login_view(request):
    User = get_user_model()
    username = request.data.get("encodedUsername")

    username = decode_username(username)

    # Create user if not exists
    user, created = User.objects.get_or_create(username=username)

    # Check if user exists after creation
    if user_exists(username):
        return Response({
            "message": "User exists",
            "username": username,
            "is_new_user": created
        }, status=200)
    else:
        return Response({
            "message": "User does not exist",
            "username": username
        }, status=401)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        return Response({"message": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

# Initialize the Azure OpenAI client
client = ChatCompletionsClient(
    endpoint=settings.OPENAI_ENDPOINT,
    credential=AzureKeyCredential(settings.OPENAI_API_KEY)
)

def validate_goal(goal_data, aligned_objectives=None):
    log_goal_submission(goal_data)
    
    # Calculate alignment percentage if objectives are provided
    alignment_info = None
    if aligned_objectives and aligned_objectives.exists():
        # Use LLM-based alignment calculation
        from django.conf import settings
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential
        
        azure_client = ChatCompletionsClient(
            endpoint=settings.OPENAI_ENDPOINT,
            credential=AzureKeyCredential(settings.OPENAI_API_KEY)
        )
        
        try:
            alignment_info = calculate_alignment_with_llm(
                goal_data,
                list(aligned_objectives),
                azure_client,
                settings.OPENAI_MODEL_NAME
            )
            logger.info(f"✅ LLM-based alignment calculation successful")
        except Exception as e:
            logger.error(f"❌ LLM alignment failed: {str(e)}")
            logger.info("Falling back to SequenceMatcher...")
            alignment_info = calculate_alignment_percentage(
                goal_data.get('goal', ''),
                list(aligned_objectives)
            )
        
        # Print detailed comparison data for debugging
        logger.info("\n" + "="*80)
        logger.info("=== DATABASE VALUES FETCHED FOR LLM COMPARISON ===")
        logger.info("="*80)
        logger.info(f"USER GOAL TO COMPARE: {goal_data.get('goal', '')}")
        logger.info(f"USER MEASURE OF SUCCESS: {goal_data.get('measure_of_success', '')}")
        logger.info("\nFETCHED BU OBJECTIVES FROM DATABASE:")
        for idx, obj in enumerate(aligned_objectives, 1):
            logger.info(f"\n{idx}. BU: {obj.org_unit.name}")
            logger.info(f"   TA: {obj.thrust_area} (Raw: {obj.linkage_ta_raw})")
            logger.info(f"   GO: {obj.group_objective} (Raw: {obj.linkage_go_raw})")
            logger.info(f"   OBJECTIVE TEXT: {obj.goal_text}")
            logger.info(f"   MEASURE OF SUCCESS: {obj.measure_of_success or 'Not specified'}")
            logger.info(f"   SOURCE: {obj.source_sheet}, Row {obj.source_row_no}")
        logger.info("\n" + "="*80)
        logger.info("=== LLM WILL COMPARE THESE VALUES ===")
        logger.info("="*80)
        
        # NEW: Display detailed matched objectives with similarity scores
        if alignment_info and 'matched_by_bu' in alignment_info:
            logger.info("\n" + "#"*80)
            logger.info("### DETAILED CROSSLINKED BU COMPARISON RESULTS ###")
            logger.info("#"*80)
            logger.info(f"\nUSER BU: {goal_data.get('user_bu', 'Not specified')}")
            logger.info(f"CROSSLINKED BUs: {', '.join(goal_data.get('crosslinked_bus', []))}")
            logger.info(f"\nOVERALL ALIGNMENT: {alignment_info['overall_alignment']}%")
            logger.info(f"TOTAL OBJECTIVES COMPARED: {alignment_info['total_objectives']}")
            
            for bu_name, matches in alignment_info['matched_by_bu'].items():
                bu_percentage = alignment_info['bu_alignment_percentages'].get(bu_name, 0)
                logger.info("\n" + "-"*80)
                logger.info(f"BUSINESS UNIT: {bu_name}")
                logger.info(f"BU ALIGNMENT PERCENTAGE: {bu_percentage}%")
                logger.info(f"NUMBER OF MATCHED OBJECTIVES: {len(matches)}")
                logger.info("-"*80)
                
                for idx, match in enumerate(matches, 1):
                    logger.info(f"\n  Match #{idx}:")
                    logger.info(f"  Similarity Score: {match['similarity_percentage']}%")
                    logger.info(f"  Thrust Area: {match['thrust_area']}")
                    logger.info(f"  Group Objective: {match['group_objective']}")
                    logger.info(f"  Parameter: {match['parameter_name']}")
                    logger.info(f"  Objective Text: {match['objective_text']}")
                    logger.info(f"  Measure of Success: {match['measure_of_success']}")
                    logger.info(f"  Source: {match['source_sheet']}, Row {match['source_row']}")
                    logger.info(f"  Relevance: {'HIGH' if match['similarity_percentage'] > 70 else 'MEDIUM' if match['similarity_percentage'] > 40 else 'LOW'}")
            
            logger.info("\n" + "#"*80)
            logger.info("### END OF CROSSLINKED BU COMPARISON ###")
            logger.info("#"*80 + "\n")
    # Create a prompt with clear HTML structure (include user's MoS for SMART evaluation)
    prompt = (
        "User entered Goal Details for Evaluation:<br>"
        "<p><strong>Goal:</strong> {goal}</p>"
        "<p><strong>Measure of Success:</strong> {measure_of_success}</p>"
        "<p><strong>KPI Metrics:</strong> {kpi_metrics}</p>"
        "<p><strong>Outcome Defined (Yes/No):</strong> {outcome_defined}</p>"
        "<p><strong>Quantifiable Objective:</strong> {quantifiable_objective}</p>"
        "<p><strong>Skills Available (Yes/No):</strong> {skills_available}</p>"
        "<p><strong>Obstacles Considered (Yes/No):</strong> {obstacles_considered}</p>"
        "<p><strong>Thrust Area:</strong> {thrust_area}</p>"
        "<p><strong>Start Date:</strong> {start_date}</p>"
        "<p><strong>End Date:</strong> {end_date}</p>"
    ).format(
        goal=goal_data.get("goal", ""),
        measure_of_success=goal_data.get("measure_of_success", ""),
        kpi_metrics=goal_data.get("kpi_metrics", ""),
        outcome_defined=goal_data.get("outcome_defined", ""),
        quantifiable_objective=goal_data.get("quantifiable_objective", ""),
        skills_available=goal_data.get("skills_available", ""),
        obstacles_considered=goal_data.get("obstacles_considered", ""),
        thrust_area=goal_data.get("thrust_area", ""),
        start_date=goal_data.get("start_date", ""),
        end_date=goal_data.get("end_date", "")
    )
    
    # Add BU alignment data to prompt
    if aligned_objectives and aligned_objectives.exists():
        # Group objectives by BU for clearer presentation
        objectives_by_bu = {}
        for obj in aligned_objectives:
            bu_name = obj.org_unit.name if obj.org_unit else 'Unknown'
            if bu_name not in objectives_by_bu:
                objectives_by_bu[bu_name] = []
            objectives_by_bu[bu_name].append(obj)
        
        prompt += "<br><br><strong>Related BU Objectives for LLM Comparison and Alignment Analysis:</strong><br>"
        prompt += f"<p><em>Found {aligned_objectives.count()} matching objectives across {len(objectives_by_bu)} Business Units.</em></p>"
        
        # Only include objective summaries, not full text
        for bu_name, objectives in objectives_by_bu.items():
            prompt += f"<p><strong>{bu_name} BU:</strong> {len(objectives)} aligned objectives</p>"
        
        logger.info(f"Added {aligned_objectives.count()} BU objectives from {len(objectives_by_bu)} BUs to AI prompt for comparison")
    
    if alignment_info:
        prompt += f"<br><br><strong>Pre-calculated Alignment Score:</strong> {alignment_info['overall_alignment']}%<br>"
        prompt += "<p><em>Please use this as reference but perform your own detailed comparison analysis.</em></p>"
        logger.info(f"Added alignment score to prompt: {alignment_info['overall_alignment']}%")
    
    logger.info(f"Complete prompt length: {len(prompt)} characters")

    response = client.complete(
        messages=[
            SystemMessage(content="""You are an AI assistant specializing in SMART goal evaluation.
                                        Assess the goal based on its Specificity, Measurability, Achievability, Relevance, and Time-Bound nature.
                                        Analyze the following employee goal using the SMART criteria (Specific, Measurable, Achievable, Relevant, and Time-Bound).
                                        
                                        IMPORTANT: When BU objectives are provided, YOU MUST perform detailed comparison analysis:
                                        1. Compare the user's goal text with each BU objective text
                                        2. Calculate similarity and alignment percentages for each BU objective
                                        3. Identify overlapping themes, keywords, and objectives
                                        4. Assess how well the user's goal aligns with organizational objectives
                                        5. Provide specific alignment scores for each BU objective
                                        
                                        Internally calculate an overall SMARTness percentage based on equal weightage (20 each).
                                        As well as measure the Goal alignment to Group objective and Thrust Areas on the scale of 10.
                                        
                                        When BU objectives are provided, perform YOUR OWN comparison analysis and provide:
                                        - Individual alignment percentage with each BU objective
                                        - Overall BU alignment score
                                        - Specific recommendations based on BU objective comparison
                                        
                                        Do NOT show any calculations or scores in your output.
                                        Return your output in well-formatted HTML that includes proper spaces, punctuation, and line breaks.
                                        Ensure each section is wrapped in appropriate HTML tags (such as <p> and <ol>/<li>) for clear readability.
                                        
                                        For BU alignment analysis, use HTML table format for better display:
                                        
                                        Response Format:
                                        <p><strong>Message to User:</strong> Provide a concise message summarizing the goal assessment.</p>
                                        <p><strong>Your Goal SMARTness Percentage:</strong> [X]%</p>
                                        <p><strong>Goal Alignment to Thrust area:</strong> [X] out of 10.</p>
                                        <p><strong>Goal Alignment to Group Objective:</strong> [X] out of 10.</p>
                                        
                                        <p><strong>BU Alignment Analysis:</strong></p>
                                        <table border='1' style='border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 14px;'>
                                        <thead>
                                        <tr style='background-color: #f0f0f0;'>
                                        <th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Business Unit</th>
                                        <th style='padding: 8px; text-align: center; border: 1px solid #ddd;'>Alignment %</th>
                                        <th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Key Alignment Points</th>
                                        <th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Recommendations</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        [For each BU, create ONE row with this EXACT format:
                                        <tr>
                                        <td style='padding: 8px; border: 1px solid #ddd; vertical-align: top;'>[BU Name]</td>
                                        <td style='padding: 8px; border: 1px solid #ddd; text-align: center; vertical-align: top;'>[XX]%</td>
                                        <td style='padding: 8px; border: 1px solid #ddd; vertical-align: top;'>• [Point 1]<br>• [Point 2]<br>• [Point 3]</td>
                                        <td style='padding: 8px; border: 1px solid #ddd; vertical-align: top;'>• [Recommendation 1]<br>• [Recommendation 2]</td>
                                        </tr>]
                                        </tbody>
                                        </table>
                                        
                                        IMPORTANT: Use EXACTLY this table format. Each BU gets ONE row. Use bullet points (•) and <br> tags for multiple items in cells.
                                        <p><strong>Recommendations:</strong> If the percentage is below 75, list actionable steps to improve it. 
                                        If the SMARTness is 75 or above, confirm that the goal meets SMART criteria.
                                        If below 75, provide specific, concise, and numbered recommendations to improve it.
                                        Include recommendations based on BU objective comparison when available.</p>
                                        <p>Recommendation Format:</p>
                                        <ol>
                                        <li><strong>Specificity:</strong> [Recommendation]</li>
                                        <li><strong>Measurability:</strong> [Recommendation]</li>
                                        <li><strong>Achievability:</strong> [Recommendation]</li>
                                        <li><strong>Relevance:</strong> [Recommendation]</li>
                                        <li><strong>Time-Bound:</strong> [Recommendation]</li>
                                        <li><strong>Overall:</strong> [Recommendation]</li>
                                        </ol>
                                        <p><strong>Suggestions:</strong> Rewrite the Goal and Measure of Success in such a way so that the same goal can achieve better Smartness as well as to improve the Goal alignment to Group objective and Thrust areas.</p>

                                        """),
            UserMessage(content=prompt)
        ],
        model=settings.OPENAI_MODEL_NAME,
        max_tokens=2500,
        stream=True
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta:
            yield chunk.choices[0].delta.content

@api_view(["POST"])
def submit_goal(request):
    try:
        username = request.data.get("loginUser")
        username = decode_username(username)
        if not username:
            return Response({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Auto-create user if not exists (for local testing)
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username) 
        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")

        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError) as e:
            print("Date Parsing Error:", e)
            return Response({"message": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        goal_data = {
            "goal": request.data.get("goal"),
            "measure_of_success": request.data.get("measure_of_success"),
            "kpi_metrics": request.data.get("kpi_metrics"),
            "outcome_defined": request.data.get("outcome_defined"),
            "quantifiable_objective": request.data.get("quantifiable_objective"),
            "skills_available": request.data.get("skills_available"),
            "obstacles_considered": request.data.get("obstacles_considered"),
            "thrust_area": request.data.get("thrust_area"),
            "sub_category": request.data.get("sub_category"),
            "group_objectives": request.data.get("group_objectives"),
            "additional_sub_category": request.data.get("additional_sub_category"),
            "user_bu": request.data.get("user_bu"),
            "crosslinked_bus": request.data.get("crosslinked_bus", []),
            "start_date": start_date,
            "end_date": end_date,
        }
        print("data from frontend : ",goal_data)

        goal_id = request.data.get("goalId") 
        if any(value is None for value in goal_data.values()):
            return Response({"message": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
        def event_stream():
            try:
                temp_goal = SmartGoal(
                    user=user,
                    goal=goal_data["goal"],
                    measure_of_success=goal_data["measure_of_success"],
                    kpi_metrics=goal_data["kpi_metrics"],
                    outcome_defined=goal_data["outcome_defined"],
                    quantifiable_objective=goal_data["quantifiable_objective"],
                    skills_available=goal_data["skills_available"],
                    obstacles_considered=goal_data["obstacles_considered"],
                    thrust_area=goal_data["thrust_area"],
                    sub_category=goal_data["sub_category"],
                    group_objectives=goal_data["group_objectives"],
                    additional_sub_category=goal_data["additional_sub_category"],
                    user_bu=goal_data["user_bu"],
                    crosslinked_bus=goal_data["crosslinked_bus"],
                    start_date=goal_data["start_date"],
                    end_date=goal_data["end_date"],
                    response=""
                )

                aligned_objs = temp_goal.get_aligned_objectives()
                logger.info(f"Found {aligned_objs.count()} aligned objectives for analysis")

                response_text = []
                try:
                    for chunk in validate_goal(goal_data, aligned_objs):
                        yield f"{chunk}"
                        response_text.append(chunk)
                except Exception as ai_error:
                    logger.error(f"AI API Error: {str(ai_error)}")
                    error_msg = (
                        "<p style='color: red;'><strong>⚠️ AI Service Error</strong></p>"
                        "<p>Unable to connect to AI service. This could be due to:</p>"
                        "<ul>"
                        "<li>Network connectivity issues</li>"
                        "<li>Azure service timeout</li>"
                        "<li>API rate limits</li>"
                        "</ul>"
                        f"<p><strong>Found {aligned_objs.count()} matching BU objectives:</strong></p>"
                    )
                    yield error_msg
                    
                    # Show aligned objectives even if AI fails
                    if aligned_objs.exists():
                        for idx, obj in enumerate(aligned_objs[:5], 1):
                            yield f"<p>{idx}. <strong>{obj.org_unit.name}</strong>: {obj.goal_text[:100]}...</p>"
                    
                    yield "<p>Please try again or contact support if the issue persists.</p>"
                    response_text.append(error_msg)

                full_response = "".join(response_text)

                if goal_id:
                    try:
                        existing_goal = SmartGoal.objects.get(id=goal_id, user=user)
                        for key, value in goal_data.items():
                            setattr(existing_goal, key, value)
                        existing_goal.response = full_response
                        existing_goal.save()
                    except SmartGoal.DoesNotExist:
                        pass
                else:
                    SmartGoal.objects.create(user=user, response=full_response, **goal_data)

                yield "[DONE]"
            
            except Exception as stream_error:
                logger.error(f"Stream Error: {str(stream_error)}")
                yield f"<p style='color: red;'>Error: {str(stream_error)}</p>"
                yield "[DONE]"


        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no" 
        return response

    except Exception as e:
        print("General Error:", e)
        return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size' 
    max_page_size = 100  

@api_view(['GET'])
def get_user_goals(request):
    username = request.GET.get("username") or request.query_params.get("loginUser")
    username = decode_username(username)
    
    if not username:
        return Response({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    # Auto-create user if not exists (for local testing)
    User = get_user_model()
    user, created = User.objects.get_or_create(username=username)
    goals = SmartGoal.objects.filter(user=user).order_by('-id')  # Order by latest goals

    paginator = CustomPagination()
    paginated_goals = paginator.paginate_queryset(goals, request)

    serializer = SmartGoalSerializer(paginated_goals, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["DELETE"])
def delete_smart_goal(request, goal_id):
    try:
        username = request.query_params.get("loginUser")
        username = decode_username(username)

        if not username:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Auto-create user if not exists (for local testing)
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)

        goal = SmartGoal.objects.get(id=goal_id, user=user)
        goal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  # No content in response
    except SmartGoal.DoesNotExist:
        return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET", "PUT"])
def update_smart_goal(request, goal_id):
    try:
        username = request.query_params.get("loginUser")
        username = decode_username(username)


        if not username:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        # Auto-create user if not exists (for local testing)
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        goal = SmartGoal.objects.get(id=goal_id, user=user)

        if request.method == "GET":
            serializer = SmartGoalSerializer(goal)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == "PUT":
            serializer = SmartGoalSerializer(goal, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Goal updated successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except SmartGoal.DoesNotExist:
        return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["POST"])
def final_goal(request):
    username = request.data.get("loginUser")
    username = decode_username(username)

    goal_id = request.data.get("goal_id")  
    final_goal_confirmed = request.data.get("final_goal_confirmed")

    if not username:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    if final_goal_confirmed is None:
        return Response({"error": "Missing final_goal_confirmed field"}, status=400)
    
    # Auto-create user if not exists (for local testing)
    User = get_user_model()
    user, created = User.objects.get_or_create(username=username)

    try:
        if goal_id:  
            smart_goal = SmartGoal.objects.filter(id=goal_id, user=user).first()
        else:
            smart_goal = SmartGoal.objects.filter(user=user).last()

        if not smart_goal:
            return Response({"error": "No existing goal found for this user"}, status=404)

        smart_goal.final_goal = final_goal_confirmed
        smart_goal.save()

        return Response({"message": "Final goal confirmed successfully"}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
def get_goal_alignment(request, goal_id):
    """Get aligned BU objectives for a specific goal with alignment percentage"""
    try:
        username = request.query_params.get("loginUser")
        username = decode_username(username)

        if not username:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)

        goal = SmartGoal.objects.get(id=goal_id, user=user)
        logger.info(f"=== GOAL ALIGNMENT REQUEST ===")
        logger.info(f"Goal ID: {goal_id}, User: {username}")
        logger.info(f"Goal: {goal.goal[:100]}...")
        
        aligned_objectives = goal.get_aligned_objectives()
        
        # Calculate alignment percentage
        from .alignment_utils import calculate_alignment_percentage
        alignment_info = None
        if aligned_objectives.exists():
            alignment_info = calculate_alignment_percentage(
                goal.goal,
                list(aligned_objectives)
            )

        response_data = {
            "goal_id": goal.id,
            "user_bu": goal.user_bu,
            "thrust_area": goal.thrust_area,
            "group_objective": goal.group_objectives,
            "crosslinked_bus": goal.crosslinked_bus or [],
            "aligned_objectives": BUObjectiveSerializer(aligned_objectives, many=True).data,
            "alignment_info": alignment_info
        }
        
        logger.info(f"Returning {len(response_data['aligned_objectives'])} aligned objectives")
        if alignment_info:
            logger.info(f"Overall Alignment: {alignment_info['overall_alignment']}%")
        logger.info(f"=== END ALIGNMENT REQUEST ===")

        return Response(response_data, status=status.HTTP_200_OK)

    except SmartGoal.DoesNotExist:
        logger.error(f"Goal {goal_id} not found for user {username}")
        return Response({"error": "Goal not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in goal alignment: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def get_filtered_group_objectives(request):
    """Get filtered group objectives based on BU, TA, and GO"""
    try:
        bu_name = request.query_params.get("bu_name")
        thrust_area = request.query_params.get("thrust_area")
        group_objective = request.query_params.get("group_objective")

        if not bu_name:
            return Response({"error": "bu_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        filters = {"bu_name": bu_name}
        if thrust_area:
            filters["thrust_area"] = thrust_area
        if group_objective:
            filters["group_objective"] = group_objective

        objectives = BUObjective.objects.filter(**filters)
        serializer = BUObjectiveSerializer(objectives, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

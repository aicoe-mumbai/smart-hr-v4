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
from .models import SmartGoal
from .serializers import SmartGoalSerializer, GoalAlignmentSerializer
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
from .gap_analysis import analyze_goal_coverage, get_recommendations

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
    if aligned_objectives:
        # Use LLM-based alignment calculation
        azure_client = ChatCompletionsClient(
            endpoint=settings.OPENAI_ENDPOINT,
            credential=AzureKeyCredential(settings.OPENAI_API_KEY)
        )
        
        try:
            alignment_info = calculate_alignment_with_llm(
                goal_data,
                list(aligned_objectives),
                azure_client,
                settings.OPENAI_MODEL_NAME,
                exclude_user_bu=True  # Exclude user's own BU from alignment
            )
            logger.info(f"✅ LLM-based alignment calculation successful")
        except Exception as e:
            logger.error(f"❌ LLM alignment failed: {str(e)}")
            logger.info("Falling back to SequenceMatcher...")
            alignment_info = calculate_alignment_percentage(
                goal_data.get('goal', ''),
                list(aligned_objectives),
                user_bu=goal_data.get('user_bu'),
                exclude_user_bu=True  # Exclude user's own BU from alignment
            )
        
        # Print detailed comparison data for debugging (goal text only, no MoS)
        logger.info("\n" + "="*80)
        logger.info("=== DATABASE VALUES FETCHED FOR LLM COMPARISON ===")
        logger.info("="*80)
        logger.info(f"USER GOAL TO COMPARE: {goal_data.get('goal', '')}")
        logger.info(f"USER MEASURE OF SUCCESS: {goal_data.get('measure_of_success', '')}")
        logger.info("\nFETCHED BU OBJECTIVES FROM DATABASE (Goal Text Only):")
        for idx, obj in enumerate(aligned_objectives, 1):
            logger.info(f"\n{idx}. BU: {obj['bu_name']}")
            logger.info(f"   TA: {obj['thrust_area_str']}")
            logger.info(f"   GO: {obj['group_objective_str']}")
            logger.info(f"   GOAL TEXT: {obj['goal_text']}")
            logger.info(f"   (Measure of Success excluded from alignment calculation)")
        logger.info("\n" + "="*80)
        logger.info("=== LLM WILL COMPARE THESE VALUES ===")
        logger.info("="*80)
        
        # NEW: Display detailed matched objectives with similarity scores (goal text only)
        if alignment_info and 'matched_by_bu' in alignment_info:
            logger.info("\n" + "#"*80)
            logger.info("### DETAILED CROSSLINKED BU COMPARISON RESULTS ###")
            logger.info("#"*80)
            logger.info(f"\nUSER BU: {goal_data.get('user_bu', 'Not specified')}")
            logger.info(f"CROSSLINKED BUs: {', '.join(goal_data.get('crosslinked_bus', []))}")
            logger.info(f"\nOVERALL ALIGNMENT: {alignment_info['overall_alignment']}%")
            logger.info(f"TOTAL OBJECTIVES COMPARED: {alignment_info['total_objectives']}")
            logger.info(f"NOTE: User's own BU ({goal_data.get('user_bu', 'N/A')}) excluded from alignment results")
            
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
                    logger.info(f"  Goal Text: {match['objective_text']}")
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
    if aligned_objectives:
        # Group objectives by BU for clearer presentation
        objectives_by_bu = {}
        for obj in aligned_objectives:
            bu_name = obj.get('bu_name', 'Unknown')
            if bu_name not in objectives_by_bu:
                objectives_by_bu[bu_name] = []
            objectives_by_bu[bu_name].append(obj)
        
        prompt += "<br><br><strong>Related BU Objectives for LLM Comparison and Alignment Analysis:</strong><br>"
        prompt += f"<p><em>Found {len(aligned_objectives)} matching objectives across {len(objectives_by_bu)} Business Units.</em></p>"
        
        # Only include objective summaries, not full text
        for bu_name, objectives in objectives_by_bu.items():
            prompt += f"<p><strong>{bu_name} BU:</strong> {len(objectives)} aligned objectives</p>"
        
        logger.info(f"Added {len(aligned_objectives)} BU objectives from {len(objectives_by_bu)} BUs to AI prompt for comparison")
    else:
        # Explicitly tell the AI that NO objectives were found
        prompt += "<br><br><strong>BU Alignment Status:</strong><br>"
        prompt += "<p style='color: red;'><em>⚠️ Found 0 matching objectives from goals database.</em></p>"
        prompt += f"<p>User selected: <strong>BU:</strong> {goal_data.get('user_bu', 'N/A')}, "
        prompt += f"<strong>Crosslinked BUs:</strong> {', '.join(goal_data.get('crosslinked_bus', [])) or 'None'}, "
        prompt += f"<strong>TA:</strong> {goal_data.get('thrust_area', 'N/A')}, "
        prompt += f"<strong>GO:</strong> {goal_data.get('group_objectives', 'N/A')}</p>"
        prompt += "<p><em>This combination of BU, TA, and GO does not have any defined objectives in the database.</em></p>"
        logger.warning("No aligned objectives found - AI will be informed to skip BU alignment table")
    
    if alignment_info:
        prompt += f"<br><br><strong>Pre-calculated Alignment Score:</strong> {alignment_info['overall_alignment']}%<br>"
        prompt += "<p><em>Please use this as reference but perform your own detailed comparison analysis.</em></p>"
        logger.info(f"Added alignment score to prompt: {alignment_info['overall_alignment']}%")
    
    logger.info(f"Complete prompt length: {len(prompt)} characters")

    try:
        response = client.complete(
            messages=[
                SystemMessage(content="""You are an AI assistant specializing in SMART goal evaluation.
                                            Assess the goal based on its Specificity, Measurability, Achievability, Relevance, and Time-Bound nature.
                                            Analyze the following employee goal using the SMART criteria (Specific, Measurable, Achievable, Relevant, and Time-Bound).
                                            
                                            Internally calculate an overall SMARTness percentage based on equal weightage (20 each).
                                            As well as measure the Goal alignment to Group objective and Thrust Areas on the scale of 10.
                                            
                                            Do NOT show any calculations or scores in your output.
                                            Return your output in well-formatted HTML that includes proper spaces, punctuation, and line breaks.
                                            Ensure each section is wrapped in appropriate HTML tags (such as <p> and <ol>/<li>) for clear readability.
                                            
                                            Response Format:
                                            <p><strong>Message to User:</strong> Provide a concise message summarizing the goal assessment.</p>
                                            <p><strong>Your Goal SMARTness Percentage:</strong> [X]%</p>
                                            <p><strong>Goal Alignment to Thrust area:</strong> [X] out of 10.</p>
                                            <p><strong>Goal Alignment to Group Objective:</strong> [X] out of 10.</p>
                                            
                                            CRITICAL INSTRUCTION FOR BU ALIGNMENT:
                                            - If the prompt explicitly states "Found 0 matching objectives" or shows no BU objectives data, DO NOT create any BU Alignment Analysis table
                                            - If BU objectives ARE provided in the prompt, ONLY THEN create the BU Alignment Analysis table
                                            - NEVER invent or hallucinate BU names or alignment data
                                            - ONLY use the actual BU names and objectives provided in the prompt
                                            - IMPORTANT: DO NOT include the user's own BU in the BU Alignment Analysis table (the system has already filtered it out)
                                            - Only show cross-linked BUs (other BUs) in the alignment table, NOT the user's own BU
                                            
                                            When BU objectives ARE provided:
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
                                            [For each BU mentioned in the prompt (excluding user's own BU), create ONE row with this EXACT format:
                                            <tr>
                                            <td style='padding: 8px; border: 1px solid #ddd; vertical-align: top;'>[BU Name from prompt]</td>
                                            <td style='padding: 8px; border: 1px solid #ddd; text-align: center; vertical-align: top;'>[XX]%</td>
                                            <td style='padding: 8px; border: 1px solid #ddd; vertical-align: top;'>• [Point 1]<br>• [Point 2]<br>• [Point 3]</td>
                                            <td style='padding: 8px; border: 1px solid #ddd; vertical-align: top;'>• [Recommendation 1]<br>• [Recommendation 2]</td>
                                            </tr>]
                                            </tbody>
                                            </table>
                                            
                                            When NO BU objectives are found:
                                            <p><strong>BU Alignment Analysis:</strong></p>
                                            <p style='color: #d9534f;'><em>⚠️ No matching BU objectives found for the selected Thrust Area and Group Objective combination. This may indicate:</em></p>
                                            <ul>
                                            <li>The selected TA/GO combination doesn't have defined objectives in the selected Business Units</li>
                                            <li>Consider reviewing your TA and GO selections</li>
                                            <li>Contact your manager or HR for guidance on appropriate TA/GO alignment</li>
                                            </ul>
                                            
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
                                            
                                            <p><strong>Suggestions:</strong> Based on the analysis above, provide improved versions of the goal and measure of success that address the identified weaknesses and enhance SMART criteria alignment. Format your response EXACTLY as follows:</p>
                                            <p><strong>Improved Goal:</strong> [Rewrite the goal text to be more specific, measurable, achievable, relevant, and time-bound. Incorporate BU alignment recommendations if applicable.]</p>
                                            <p><strong>Improved Measure of Success:</strong> [Rewrite the measure of success to include clear metrics, validation methods, and milestone tracking that align with the improved goal.]</p>

                                            """),
                UserMessage(content=prompt)
            ],
            model=settings.OPENAI_MODEL_NAME,
            max_tokens=2500,
            stream=True
        )
    except Exception as api_error:
        logger.error(f"Azure OpenAI API Error: {str(api_error)}")
        logger.error(f"Endpoint: {settings.OPENAI_ENDPOINT}")
        logger.error(f"Model: {settings.OPENAI_MODEL_NAME}")
        raise

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
                logger.info(f"Found {len(aligned_objs)} aligned objectives for analysis")

                response_text = []
                try:
                    for chunk in validate_goal(goal_data, aligned_objs):
                        yield f"{chunk}"
                        response_text.append(chunk)
                except ConnectionError as conn_error:
                    logger.error(f"Connection Error: {str(conn_error)}")
                    error_msg = (
                        "<p style='color: red;'><strong>⚠️ Connection Error</strong></p>"
                        "<p>Unable to connect to Azure OpenAI service. Please check:</p>"
                        "<ul>"
                        "<li>Network connectivity</li>"
                        "<li>Azure endpoint URL configuration</li>"
                        "<li>DNS resolution</li>"
                        "<li>Firewall settings</li>"
                        "</ul>"
                        f"<p><strong>Found {len(aligned_objs)} matching BU objectives for your goal.</strong></p>"
                    )
                    yield error_msg
                    response_text.append(error_msg)
                except Exception as ai_error:
                    logger.error(f"AI API Error: {str(ai_error)}")
                    error_msg = (
                        "<p style='color: red;'><strong>⚠️ AI Service Error</strong></p>"
                        "<p>Unable to process your goal with AI service. This could be due to:</p>"
                        "<ul>"
                        "<li>Network connectivity issues</li>"
                        "<li>Azure service timeout</li>"
                        "<li>API rate limits</li>"
                        "<li>Invalid API configuration</li>"
                        "</ul>"
                        f"<p><strong>Found {len(aligned_objs)} matching BU objectives:</strong></p>"
                    )
                    yield error_msg
                    
                    # Show aligned objectives even if AI fails
                    if aligned_objs:
                        for idx, obj in enumerate(aligned_objs[:5], 1):
                            yield f"<p>{idx}. <strong>{obj['bu_name']}</strong>: {obj['goal_text'][:100]}...</p>"
                    
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

    # Check if this is an export request - if so, skip pagination
    export_to_excel = request.query_params.get('export') == 'true'
    
    if export_to_excel:
        serializer = SmartGoalSerializer(goals, many=True)
        return Response({"results": serializer.data})
    else:
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
        
        # Check if user has any confirmed goals and if gap analysis has been done
        confirmed_goals = SmartGoal.objects.filter(user=user, final_goal="True").count()
        from .models import GapAnalysisRecord
        has_gap_analysis = GapAnalysisRecord.objects.filter(user=user).exists()
        
        return Response({
            "message": "Final goal confirmed successfully",
            "confirmed_goals_count": confirmed_goals,
            "gap_analysis_required": confirmed_goals > 0 and not has_gap_analysis,
            "has_gap_analysis": has_gap_analysis
        }, status=200)
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
        if aligned_objectives:
            alignment_info = calculate_alignment_percentage(
                goal.goal,
                aligned_objectives,
                user_bu=goal.user_bu,
                exclude_user_bu=True  # Exclude user's own BU from alignment
            )

        response_data = {
            "goal_id": goal.id,
            "user_bu": goal.user_bu,
            "thrust_area": goal.thrust_area,
            "group_objective": goal.group_objectives,
            "crosslinked_bus": goal.crosslinked_bus or [],
            "aligned_objectives": aligned_objectives,
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
        from .goals_db_utils import get_bu_objectives
        
        bu_name = request.query_params.get("bu_name")
        thrust_area = request.query_params.get("thrust_area")
        group_objective = request.query_params.get("group_objective")

        if not bu_name:
            return Response({"error": "bu_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        objectives = get_bu_objectives(
            bu_name=bu_name,
            thrust_area_filter=thrust_area,
            group_objective_filter=group_objective
        )

        return Response(objectives, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def gap_analysis_status(request):
    """Check if user has completed gap analysis"""
    try:
        username = request.query_params.get("loginUser")
        username = decode_username(username)

        if not username:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)

        from .models import GapAnalysisRecord
        has_gap_analysis = GapAnalysisRecord.objects.filter(user=user).exists()
        confirmed_goals_count = SmartGoal.objects.filter(user=user, final_goal="True").count()
        
        latest_analysis = None
        if has_gap_analysis:
            latest = GapAnalysisRecord.objects.filter(user=user).first()
            latest_analysis = {
                'date': latest.analysis_date.strftime('%Y-%m-%d %H:%M'),
                'goals_count': len(latest.goals_analyzed),
                'ta_coverage': latest.ta_coverage,
                'go_coverage': latest.go_coverage
            }

        return Response({
            "has_gap_analysis": has_gap_analysis,
            "confirmed_goals_count": confirmed_goals_count,
            "gap_analysis_required": confirmed_goals_count > 0 and not has_gap_analysis,
            "latest_analysis": latest_analysis
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error checking gap analysis status: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def gap_analysis_history(request):
    """Get all gap analysis records for a user"""
    try:
        username = request.query_params.get("loginUser")
        username = decode_username(username)

        if not username:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)

        from .models import GapAnalysisRecord
        from .serializers import GapAnalysisRecordSerializer
        
        analyses = GapAnalysisRecord.objects.filter(user=user).order_by('-analysis_date')
        serializer = GapAnalysisRecordSerializer(analyses, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching gap analysis history: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@log_execution_time
def analyze_goals_gap(request):
    """Analyze gap between selected goals and company GO/TA"""
    try:
        username = request.data.get("loginUser")
        username = decode_username(username)

        if not username:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)

        selected_goal_ids = request.data.get("goal_ids", [])
        
        if not selected_goal_ids:
            return Response({"error": "No goals selected for analysis"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Gap analysis requested by {username} for goals: {selected_goal_ids}")
        
        # Perform gap analysis
        analysis_result = analyze_goal_coverage(selected_goal_ids, user)
        
        if 'error' in analysis_result:
            return Response(analysis_result, status=status.HTTP_404_NOT_FOUND)
        
        # Generate recommendations
        recommendations = get_recommendations(analysis_result)
        analysis_result['recommendations'] = recommendations
        
        # Save gap analysis record
        from .models import GapAnalysisRecord
        GapAnalysisRecord.objects.create(
            user=user,
            goals_analyzed=selected_goal_ids,
            ta_coverage=analysis_result['coverage']['thrust_areas']['coverage_percentage'],
            go_coverage=analysis_result['coverage']['group_objectives']['coverage_percentage'],
            analysis_result=analysis_result
        )
        
        logger.info(f"Gap analysis completed: TA coverage {analysis_result['coverage']['thrust_areas']['coverage_percentage']}%, GO coverage {analysis_result['coverage']['group_objectives']['coverage_percentage']}%")
        
        return Response(analysis_result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in gap analysis: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

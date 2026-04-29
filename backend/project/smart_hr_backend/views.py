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
from .serializers import SmartGoalSerializer
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import logging
import time, base64

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

def validate_goal(goal_data):
    # Create a prompt with clear HTML structure and proper spacing
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
                                        <p><strong>Goal Alignment to Thrsut area:</strong> [X] out of 10.</p>
                                        <p><strongGoal Alignment to Group Objective:</strong> [X] out of 10.</p>
                                        <p><strong>Recommendations:</strong> If the percentage is below 75, list actionable steps to improve it. 
                                        If the SMARTness is 75 or above, confirm that the goal meets SMART criteria.
                                        If below 75, provide specific, concise, and numbered recommendations to improve it.</p>
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
        max_tokens=750,
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
        if not username or not user_exists(username):
            return Response({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        user = get_user_model().objects.get(username=username) 
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
            "start_date": start_date,
            "end_date": end_date,
        }
        print("data from frontend : ",goal_data)

        goal_id = request.data.get("goalId") 
        if any(value is None for value in goal_data.values()):
            return Response({"message": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
        def event_stream():
            response_text = []
            for chunk in validate_goal(goal_data):
                yield f"{chunk}" 
                response_text.append(chunk)

            full_response = "".join(response_text)
            
            if goal_id:
                try:
                    existing_goal = SmartGoal.objects.get(id=goal_id, user=user)
                    for key, value in goal_data.items():
                        setattr(existing_goal, key, value)  
                    existing_goal.response = full_response 
                    existing_goal.save()
                except SmartGoal.DoesNotExist:
                    print("does not exists")
            else:
                SmartGoal.objects.create(user=user, response=full_response, **goal_data)
                

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
    
    if not username or not user_exists(username):
        return Response({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    user = get_user_model().objects.get(username=username)
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

        if not username or not user_exists(username):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        user = get_user_model().objects.get(username=username)

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


        if not username or not user_exists(username):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        user = get_user_model().objects.get(username=username)
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

    if not username or not user_exists(username):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    if final_goal_confirmed is None:
        return Response({"error": "Missing final_goal_confirmed field"}, status=400)
    user = get_user_model().objects.get(username=username)

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

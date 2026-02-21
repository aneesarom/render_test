import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.logging_config import set_user_id
from app.supabase.supabase_client import supabase
from app.auth.jwt_handler import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ModelRetryMiddleware, ModelFallbackMiddleware
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_groq import ChatGroq
from app.logging_config import get_logger, set_user_id

logger = get_logger(__name__)

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5,
    max_bucket_size=5,
)

load_dotenv()


router = APIRouter(prefix="/ai", tags=["suggest"])


class SuggestRequest(BaseModel):
    title: str


class TaskDescription(BaseModel):
    description: list[str] = Field(..., description="List of suggested task descriptions", min_length=3, max_length=5)


@router.post("/suggest")
async def suggest_description(task: SuggestRequest, current_user: dict = Depends(get_current_user)):
    system_prompt = """
        You are a Senior Technical Lead responsible for defining clear and well-structured task descriptions for engineering teams.

        Your job is to translate short task titles into actionable development descriptions.

        Requirements:
        - Generate minimum 3 task descriptions.
        - Each description must contain at least 2 sentences.
        - Each description should clearly explain what will be done and how.
        - Use professional, action-oriented language.
        - Keep descriptions concise but meaningful.
        - Do not include explanations outside the JSON response.

        Return output strictly in this format:

        {
        "description": [
            "Description 1",
            "Description 2",
            "Description 3"
        ]
        }

        Examples:

        Input: "Build authentication system"

        Output:
        {
        "description": [
            "Implement a secure JWT-based authentication system for user login and registration. Integrate role-based access control to protect sensitive routes.",
            "Design and develop a scalable authentication workflow. Ensure secure password encryption and proper token validation.",
            "Create backend authentication APIs and middleware. Enforce authorization rules across protected endpoints."
        ]
        }

        Input: "Create YOLO inference API"

        Output:
        {
        "description": [
            "Develop a REST API for YOLO model inference. Handle image uploads and return structured object detection results.",
            "Implement an optimized object detection endpoint. Improve inference speed and ensure proper error handling.",
            "Containerize the YOLO inference service. Deploy it with logging, monitoring, and scalability considerations."
        ]
        }
        """

    try:
        agent = create_agent(
            model=ChatGroq(model="openai/gpt-oss-120b", temperature=0.3, rate_limiter=rate_limiter),
            tools=[],
            system_prompt=system_prompt,
            response_format=ProviderStrategy(TaskDescription),
            middleware=[
                ModelFallbackMiddleware(first_model=ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3, rate_limiter=rate_limiter))
            ]
        )

        response = await agent.ainvoke({"messages": HumanMessage(content=f"Suggest a short task description for: {task.title}")})
        output = json.loads(response["messages"][-1].content)
        logger.info("AI response generated")
        return {"task_description": output["description"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    



from enum import Enum
from pydantic import BaseModel, Field

class LeadStatusOptions(str, Enum):
    WARM = "Warm"
    COLD = "Cold"
    HOT = "Hot"

class CallAnalysis(BaseModel):
    callPurpose: str = Field(description="The primary reason for the call.")
    outcome: str = Field(description="The final result or resolution of the call.")
    customerInterest: str = Field(description="Level of interest shown by the customer (e.g., High, Medium, Low).")
    followUpRequired: bool = Field(description="Set to true if further action is required with the client.")
    nextAction: str = Field(description="The immediate next actionable step agreed upon.")
    leadStatus: LeadStatusOptions = Field(
        description="Analyze the context of the call and infer the lead status based on customer response."
    )
    summary: str = Field(description="A concise summary of what was discussed.")
    full_transcript: str = Field(description="The complete conversation transcript translated into English, formatted line-by-line as 'Agent: ...' and 'User: ...'")
    total_duration_seconds: int = Field(description="Estimated total duration of the call in seconds.")
    agent_talk_time_seconds: int = Field(description="Estimated total time the agent was speaking in seconds.")
    customer_talk_time_seconds: int = Field(description="Estimated total time the customer was speaking in seconds.")

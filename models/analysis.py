from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

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

class AnalyzeUrlRequest(BaseModel):
    url: HttpUrl
    api_key: str | None = Field(default=None, description="Exotel API Key")
    api_token: str | None = Field(default=None, description="Exotel API Token")
    headers: dict[str, str] | None = Field(default=None)

class AnalyzeUrlRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
                },
                {
                    "url": "https://recordings.exotel.com/exotelrecordings/account/recording.mp3",
                    "api_key": "your_exotel_api_key",
                    "api_token": "your_exotel_api_token"
                }
            ]
        }
    )

    url: HttpUrl = Field(
        ...,
        description="The remote HTTP/HTTPS URL of the call recording to analyze."
    )
    api_key: str | None = Field(
        default=None,
        description="Optional API key for Basic Auth (e.g. Exotel API Key)."
    )
    api_token: str | None = Field(
        default=None,
        description="Optional API token for Basic Auth (e.g. Exotel API Token)."
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Optional HTTP headers to include when fetching the recording URL."
    )
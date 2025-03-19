from typing import Literal
from pydantic import BaseModel, Field


class Router(BaseModel):
    reasoning: str = Field(
        description="Step-by-step reasoning behind the classification"
    )
    classification: Literal["ignroe", "answer", "notify"] = Field(
        description="The classification of an email: 'ignore' for irrelevant emails."
        "'notify' for important information that doesn't need a response."
        "'answer' for emails that need a reply",
    )

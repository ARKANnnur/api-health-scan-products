from typing import Literal

from pydantic import BaseModel


class ConsentAcceptRequest(BaseModel):
    disclaimer_version: str
    action: Literal["accepted"] = "accepted"


class ConsentAcceptResponse(BaseModel):
    accepted: bool
    disclaimer_version: str
    accepted_at: str


class ConsentStatusResponse(BaseModel):
    current_version: str
    accepted_version: str | None
    requires_consent: bool

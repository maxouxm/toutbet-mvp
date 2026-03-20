from __future__ import annotations

import datetime as dt
import re
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


Role = Literal["user", "admin"]
Outcome = Literal["yes", "no"]
MarketStatus = Literal["open", "resolved"]


class Msg(BaseModel):
    message: str


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    accept_terms: bool


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role
    balance_tokens: int


class MeOut(UserOut):
    pass


class FundingIn(BaseModel):
    amount_eur: int = Field(gt=0, le=1_000_000)


# Regex détectant toute balise HTML (ex. <script>, <img onerror=...>)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


class MarketCreateIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=10_000)

    @field_validator("title", "description")
    @classmethod
    def no_html_tags(cls, v: str) -> str:
        """Rejette tout champ contenant des balises HTML (prévention XSS stocké)."""
        if _HTML_TAG_RE.search(v):
            raise ValueError("Les balises HTML ne sont pas autorisées dans ce champ")
        return v


class MarketOut(BaseModel):
    id: int
    creator_id: int
    title: str
    description: str
    status: MarketStatus
    resolved_outcome: Optional[Outcome] = None
    resolved_at: Optional[dt.datetime] = None
    yes_pool: int
    no_pool: int
    created_at: dt.datetime

    prob_yes: float
    prob_no: float


class BetCreateIn(BaseModel):
    side: Outcome
    amount_tokens: int = Field(gt=0, le=1_000_000)


class BetOut(BaseModel):
    id: int
    user_id: int
    market_id: int
    side: Outcome
    amount_tokens: int
    created_at: dt.datetime
    settled: bool
    won: Optional[bool]
    payout_tokens: Optional[int]


class MyBetOut(BaseModel):
    bet: BetOut
    market: MarketOut


class ResolveIn(BaseModel):
    outcome: Outcome


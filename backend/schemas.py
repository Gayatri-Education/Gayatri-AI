from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if (
            value.count("@") != 1
            or "." not in value.split("@")[1]
            or any(c.isspace() for c in value)
        ):
            raise ValueError("Enter a valid email address")
        return value


class Register(Credentials):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value):
        if not value.strip():
            raise ValueError("Name is required")
        return value.strip()


class PaperRequest(BaseModel):
    exam_id: int
    mode: Literal["practice", "mock"] = "practice"
    year: int | None = Field(default=None, ge=2015, le=2026)


class AnswerRequest(BaseModel):
    question_id: int
    selected_option: Literal["A", "B", "C", "D"] | None


class ReviewRequest(BaseModel):
    accepted_options: list[Literal["A", "B", "C", "D"]] | None = Field(
        default=None, min_length=1, max_length=4
    )
    correct_option: Literal["A", "B", "C", "D"]
    answer_key_source: str = Field(min_length=5, max_length=2000)
    explanation: str = Field(min_length=5, max_length=20000)
    confirm_source_reviewed: bool
    version: int = Field(ge=1)

    @field_validator("answer_key_source", "explanation")
    @classmethod
    def meaningful(cls, value):
        if len(value.strip()) < 5:
            raise ValueError("Provide a meaningful review value")
        return value.strip()

    @model_validator(mode="after")
    def valid_accepted_options(self):
        if self.accepted_options is None:
            self.accepted_options = [self.correct_option]
        if self.correct_option not in self.accepted_options or len(
            set(self.accepted_options)
        ) != len(self.accepted_options):
            raise ValueError(
                "Accepted options must be unique and include the primary key"
            )
        return self

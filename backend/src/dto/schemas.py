from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=6, max_length=256)
    inviteCode: str | None = None
    id: str | None = None


class UserCredentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class PatientInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    birthDate: str = ""
    relationship: str = ""
    notes: str = ""


class InviteCreateInput(BaseModel):
    role: Literal["Familiar", "Administrador"]
    name: str = ""


class MedicationInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    name: str


class MedicationScheduleQuery(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    timezone: str = Field(min_length=1, max_length=100)


class DoseActionInput(MedicationScheduleQuery):
    doseId: str = Field(min_length=1)


class DoseUndoInput(BaseModel):
    doseId: str = Field(min_length=1)


class StockReplenishmentInput(BaseModel):
    quantity: float = Field(gt=0)
    description: str = ""


class MedicationAssistantAnswerInput(BaseModel):
    step: Literal[
        "medication",
        "startDate",
        "continuous",
        "endDate",
        "stockQuantity",
        "stockUnit",
        "unitsPerDose",
        "minimumStock",
        "instructions",
        "finished",
    ]
    answer: str = Field(min_length=1, max_length=2000)
    draft: dict[str, Any]


class DiaryRecordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    observation: str = Field(max_length=10000)
    createdAt: str
    updatedAt: str | None = None
    imageData: str | None = Field(default=None, max_length=12_000_000)
    timezone: str = Field(default="UTC", min_length=1, max_length=100)

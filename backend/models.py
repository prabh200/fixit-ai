from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class Cause(BaseModel):
    issue: str
    likelihood: Literal["High", "Medium", "Low"]
    explanation: str

class Diagnosis(BaseModel):
    category: str
    appliance_or_area: str
    problem_summary: str
    safety_level: Literal["Emergency", "Caution", "Routine"]
    immediate_action: str
    possible_causes: List[Cause] = Field(default_factory=list)
    safe_checks: List[str] = Field(default_factory=list)
    professional_help_recommended: bool = True
    cost_min_usd: Optional[int] = None
    cost_max_usd: Optional[int] = None
    cost_note: str = "Illustrative planning range, not a contractor quote."
    follow_up_questions: List[str] = Field(default_factory=list)

class RepairRequest(BaseModel):
    customer_name: str = "Hackathon demo user"
    location: str
    category: str
    problem_summary: str
    diagnosis_id: Optional[str] = None
    preferred_contact: Optional[str] = None
    selected_provider: Optional[str] = None
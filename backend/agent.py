import json
import os
from pathlib import Path
from ollama import chat
from models import Diagnosis
from tools import estimate_cost, emergency_check

SYSTEM_PROMPT = """
You are FixIt AI, a cautious household maintenance triage agent.
You can help with appliances, plumbing, electrical, HVAC, roofing, carpentry,
pest control, and general home maintenance.

You are NOT a licensed contractor, electrician, plumber, HVAC technician,
or emergency responder. Never present a guess as a confirmed diagnosis.
Use the image only as supporting evidence; symptoms and model numbers matter.

SAFETY:
- If the user reports gas smell, smoke, fire, sparking, burning smell,
  carbon monoxide alarm, or flooding near electricity, classify as Emergency.
- For gas smell: tell the user to leave immediately, avoid switches/flames,
  and contact emergency services or the gas utility from a safe location.
- For smoke/fire/sparking: tell the user to move away, avoid touching equipment,
  and contact emergency services if there is immediate danger.
- Never instruct users to open electrical panels, touch live wiring,
  bypass safety devices, handle refrigerants, work on gas lines, climb roofs,
  or dismantle pressurized systems.
- For electrical, gas, structural, roof, and serious plumbing hazards,
  recommend a qualified professional.
- Offer only low-risk visual checks or user-manual checks.
- Ask clarifying questions when evidence is insufficient.

Return ONLY a JSON object matching the requested schema.
Use concise, practical language. Set cost values to null if the category is
unclear. Cost ranges are only planning estimates, never verified quotes.
"""

def diagnose(appliance_or_area: str, category: str, description: str, image_path: str | None):
    model = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")
    emergency_terms = emergency_check(description)

    if emergency_terms:
        return Diagnosis(
            category=category,
            appliance_or_area=appliance_or_area,
            problem_summary=description[:220],
            safety_level="Emergency",
            immediate_action=(
                "Stop troubleshooting and move to a safe location. "
                "If there is immediate danger, contact emergency services. "
                "For a suspected gas leak, leave the building and contact the gas utility "
                "from outside. Do not operate switches or flames."
            ),
            possible_causes=[],
            safe_checks=[],
            professional_help_recommended=True,
            cost_min_usd=None,
            cost_max_usd=None,
            cost_note="No estimate provided because safety takes priority."
        )

    user_prompt = f"""
Appliance or area: {appliance_or_area}
Repair category: {category}
User's description: {description}

Return JSON with these exact keys:
category, appliance_or_area, problem_summary, safety_level,
immediate_action, possible_causes (array of objects with issue, likelihood,
explanation), safe_checks (array of strings),
professional_help_recommended, cost_min_usd, cost_max_usd,
cost_note, follow_up_questions (array of strings).

Use safety_level Routine or Caution. Never output Emergency unless a serious
hazard is identified. Do not invent a precise part failure.
"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    if image_path:
        messages[1]["images"] = [image_path]

    response = chat(
        model=model,
        messages=messages,
        format=Diagnosis.model_json_schema(),
        options={"temperature": 0.1}
    )
    raw = response.message.content
    parsed = json.loads(raw)
    result = Diagnosis.model_validate(parsed)

    if result.cost_min_usd is None or result.cost_max_usd is None:
        estimate = estimate_cost(category)
        result.cost_min_usd = estimate["minimum_usd"]
        result.cost_max_usd = estimate["maximum_usd"]
        result.cost_note = estimate["disclaimer"]

    return result

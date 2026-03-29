from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def build_profile_context(profile: dict) -> str:
    """Convert profile data into a readable context string for the AI"""
    return f"""
CANDIDATE PROFILE:
- Name: {profile.get('full_name', 'N/A')}
- Degree: {profile.get('degree', 'N/A')} in {profile.get('field_of_study', 'N/A')}
- University: {profile.get('university', 'N/A')}
- GPA: {profile.get('gpa', 'N/A')}
- Graduation Year: {profile.get('graduation_year', 'N/A')}
- Skills: {', '.join(profile.get('skills') or [])}
- Languages: {', '.join(profile.get('languages') or [])}
- Certifications: {', '.join(profile.get('certifications') or [])}
- Work Experience: {profile.get('work_experience') or 'None listed'}
- Target Countries: {', '.join(profile.get('target_countries') or [])}
- CV Text: {profile.get('cv_raw_text') or 'No CV uploaded yet'}
"""

def generate_cover_letter(profile: dict, job_ad: str) -> str:
    profile_context = build_profile_context(profile)

    prompt = f"""
You are an expert career coach and professional writer.

Using the candidate profile below, write a compelling cover letter for the job advertisement provided.

Rules:
- Be specific and personalized — use actual details from the profile
- Match the tone of the job advertisement
- Keep it to 3-4 paragraphs
- Do not invent qualifications not present in the profile
- End with a confident closing

{profile_context}

JOB ADVERTISEMENT:
{job_ad}

Write the cover letter now:
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content


def generate_motivation_letter(profile: dict, job_ad: str) -> str:
    profile_context = build_profile_context(profile)

    prompt = f"""
You are an expert academic and professional writer.

Using the candidate profile below, write a strong motivation letter for the position described in the job advertisement.

Rules:
- Focus on motivation, passion, and fit
- Be specific about why this role/program aligns with their goals
- Keep it to 3-4 paragraphs
- Do not invent qualifications not in the profile
- Academic tone if it's a university/PhD application, professional tone if it's a job

{profile_context}

JOB ADVERTISEMENT:
{job_ad}

Write the motivation letter now:
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content


def generate_sop(profile: dict, job_ad: str) -> str:
    profile_context = build_profile_context(profile)

    prompt = f"""
You are an expert academic writer specializing in graduate school applications.

Using the candidate profile below, write a Statement of Purpose (SOP) for the program described.

Rules:
- Start with a compelling opening about their academic journey
- Highlight relevant research, projects, and experience
- Explain why this specific program fits their goals
- End with future plans and career goals
- Keep it to 4-5 paragraphs
- Do not invent anything not in the profile

{profile_context}

PROGRAM/JOB ADVERTISEMENT:
{job_ad}

Write the Statement of Purpose now:
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500
    )

    return response.choices[0].message.content


def detect_document_type(job_ad: str) -> str:
    """Ask AI to detect what document type is needed from the job ad"""
    prompt = f"""
Read this job/program advertisement and identify what document is being requested.

Reply with ONLY one of these exact words:
- cover_letter
- motivation_letter  
- sop

Advertisement:
{job_ad}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10
    )

    result = response.choices[0].message.content.strip().lower()

    # Fallback if AI returns something unexpected
    if "sop" in result or "statement" in result:
        return "sop"
    elif "motivation" in result:
        return "motivation_letter"
    else:
        return "cover_letter"
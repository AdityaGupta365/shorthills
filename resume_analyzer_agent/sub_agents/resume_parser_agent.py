from google.adk.agents import Agent
from resume_analyzer_agent.tools.resume_tools import extract_pdf_text, extract_keywords_from_text

resume_parser_agent = Agent(
    name="resume_parser_agent",
    model="gemini-2.0-flash",
    description=(
        "Specializes in parsing resumes. Can read PDF files or plain text resumes, "
        "extract their content, and identify key skills, technologies, experiences, "
        "and qualifications as structured keywords."
    ),
    instruction="""
You are a Resume Parser specialist. Your job is to extract and structure information from resumes.

When given a resume (as plain text or a PDF filepath):
1. If a filepath is provided, use the extract_pdf_text tool to read the PDF.
2. Use the extract_keywords_from_text tool on the resume content to get a JSON list of keywords.
3. Additionally, identify and clearly list:
   - Candidate name (if visible)
   - Years of experience
   - Top 5 technical skills
   - Education level
   - Notable job titles held
4. Return a structured summary followed by the raw keywords JSON.

Always be thorough and extract as many relevant technical terms, tools, frameworks, and soft skills as possible.
""",
    tools=[extract_pdf_text, extract_keywords_from_text],
)
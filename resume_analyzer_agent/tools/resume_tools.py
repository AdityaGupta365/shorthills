import re
import os
import json
from typing import Optional
from datetime import datetime


def extract_pdf_text(filepath: str) -> str:
    """
    Extracts raw text from a PDF file at the given filepath.

    Args:
        filepath: Absolute or relative path to the PDF file.

    Returns:
        Extracted text content as a string, or an error message.
    """
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages_text).strip()
    except ImportError:
        return "Error: pdfplumber is not installed. Run: pip install pdfplumber"
    except FileNotFoundError:
        return f"Error: File not found at path: {filepath}"
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"


def extract_keywords_from_text(text: str, top_n: int = 40) -> str:
    """
    Extracts the most relevant keywords and technical terms from a given text.
    Filters out common stop words and returns a JSON list of keywords.

    Args:
        text: The input text to extract keywords from.
        top_n: Maximum number of keywords to return (default: 40).

    Returns:
        A JSON string containing a list of extracted keywords.
    """
    stop_words = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "shall", "should", "may", "might", "must", "can", "could", "not",
        "no", "nor", "so", "yet", "both", "either", "neither", "each",
        "than", "then", "that", "this", "these", "those", "i", "you", "he",
        "she", "we", "they", "it", "me", "him", "her", "us", "them", "my",
        "your", "his", "its", "our", "their", "what", "which", "who", "whom",
        "when", "where", "why", "how", "all", "any", "few", "more", "most",
        "other", "some", "such", "only", "own", "same", "as", "if", "also",
        "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "up", "about", "against", "while", "per", "etc",
    }

    text_lower = text.lower()
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#\.\-]*\b', text_lower)

    freq = {}
    for word in words:
        if word not in stop_words and len(word) > 2:
            freq[word] = freq.get(word, 0) + 1

    multi_word_patterns = re.findall(
        r'\b(?:[A-Z][a-z]+\s+){1,3}[A-Z][a-z]+\b', text
    )
    for phrase in multi_word_patterns:
        phrase_lower = phrase.lower().strip()
        if phrase_lower not in stop_words:
            freq[phrase_lower] = freq.get(phrase_lower, 0) + 2

    sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    top_keywords = [kw for kw, _ in sorted_keywords[:top_n]]

    return json.dumps(top_keywords)


def calculate_match_score(resume_keywords_json: str, jd_keywords_json: str) -> str:
    """
    Calculates a match score between resume keywords and job description keywords.
    Returns a JSON object with the score, matched keywords, and missing keywords.

    Args:
        resume_keywords_json: JSON string list of keywords extracted from the resume.
        jd_keywords_json: JSON string list of keywords extracted from the job description.

    Returns:
        A JSON string containing match_score (%), matched_keywords, and missing_keywords.
    """
    try:
        resume_keywords = set(json.loads(resume_keywords_json))
        jd_keywords = set(json.loads(jd_keywords_json))
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON input: {str(e)}"})

    if not jd_keywords:
        return json.dumps({"error": "Job description keywords list is empty."})

    matched = resume_keywords.intersection(jd_keywords)
    missing = jd_keywords.difference(resume_keywords)

    score = round((len(matched) / len(jd_keywords)) * 100, 2)

    result = {
        "match_score": score,
        "total_jd_keywords": len(jd_keywords),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "matched_keywords": sorted(list(matched)),
        "missing_keywords": sorted(list(missing)),
    }
    return json.dumps(result, indent=2)


def generate_markdown_report(
    candidate_name: str,
    target_role: str,
    match_score: float,
    matched_keywords: str,
    missing_keywords: str,
    suggestions: str,
    industry_insights: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Generates a structured markdown report for the resume analysis and saves it to a file.

    Args:
        candidate_name: Name of the candidate.
        target_role: The job role being targeted.
        match_score: The ATS match score as a percentage (0-100).
        matched_keywords: Comma-separated list of keywords found in both resume and JD.
        missing_keywords: Comma-separated list of keywords in JD but missing from resume.
        suggestions: Detailed improvement suggestions as plain text.
        industry_insights: Market and industry insights from web research.
        output_path: Optional file path to save the report. Defaults to 'resume_report.md'.

    Returns:
        The full markdown report as a string.
    """
    if output_path is None:
        output_path = "resume_report.md"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if match_score < 40:
        score_emoji = "🔴"
        score_label = "Poor Match"
    elif match_score < 70:
        score_emoji = "🟡"
        score_label = "Moderate Match"
    else:
        score_emoji = "🟢"
        score_label = "Strong Match"

    matched_list = "\n".join(
        f"- `{kw.strip()}`" for kw in matched_keywords.split(",") if kw.strip()
    ) or "_None found_"

    missing_list = "\n".join(
        f"- `{kw.strip()}`" for kw in missing_keywords.split(",") if kw.strip()
    ) or "_None missing — great match!_"

    report = f"""# Resume Analysis Report

**Candidate:** {candidate_name}
**Target Role:** {target_role}
**Generated:** {timestamp}

---

## ATS Match Score

{score_emoji} **{match_score}% — {score_label}**

> A score above 70% indicates a strong match with the job description.
> Scores below 40% suggest significant keyword gaps that need to be addressed.

---

## Matched Keywords

The following keywords from the job description were found in your resume:

{matched_list}

---

## Missing Keywords

The following keywords appear in the job description but are **not** in your resume.
Consider adding them where relevant and truthful:

{missing_list}

---

## Improvement Suggestions

{suggestions}

---

## Industry Insights

{industry_insights}

---

## Next Steps

1. Add the missing keywords naturally into your resume (do not keyword-stuff)
2. Update your **Skills** section with missing technical tools
3. Rewrite bullet points in **Experience** to reflect missing competencies
4. Consider getting certified in the top missing skills
5. Re-run this analyzer after updating your resume to track improvement

---

*Report generated by Smart Resume Analyzer — powered by Google ADK*
"""

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        return f"Report successfully saved to '{output_path}'.\n\n{report}"
    except Exception as e:
        return f"Warning: Could not save file ({e}). Report content:\n\n{report}"
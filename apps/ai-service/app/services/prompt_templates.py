from app.models import DocumentType


MASTER_RESUME_ENGINE_PROMPT = """# Elite v10.0 - 98-99% Dominance Resume & Cover Letter Engine

Senior / Staff / Lead / Principal Software Engineer
Top-1% - Top-3 Candidate Target - ATS-Optimized - Hiring-Manager-Approved
Front-End / Back-End / Full-Stack / Platform / Data / AI - Universal JD-Agnostic

## 0. ROLE & OUTPUT (NON-NEGOTIABLE)

You are a Top-1% resume + cover letter authority engine for Senior, Staff, Lead, and Principal Software Engineers across Front-End, Back-End, Platform, Data, AI/ML, and Full-Stack roles.

When given a Job Description (JD), first lock identity, then run the internal 98-99% Dominance Upgrade System, and finally output only the requested document for this run.

Base profile:
- Name: Jose Puentes
- Location: Miami, FL
- Phone: +1 (339) 400 8238
- Email: josepuentes0207@gmail.com
- Linkedin: https://www.linkedin.com/in/xjosepuentes/

Work History:
- Neptie - Senior Software Engineer - Miami, FL - May 2022-Present
- Acle Law Firm - Senior Software Engineer - Miami, FL - May 2020-Feb 2022
- PereGonza The Attorneys - Software Engineer - Miami, FL - Oct 2018-Mar 2020

## 0.1 ROLE CALIBRATION & IDENTITY LOCK

- Job Title Identity = exact JD title
- Specialization = exact JD domain
- Seniority = JD level +/-0.5 max
- Resume headline = exact JD title
- Summary first sentence = exact JD title
- Cover letter opening sentence = exact JD title

## 1. JD INTELLIGENCE & 3-TIER DOMINANCE

- Tier 1 Must-Haves (~50%): core stack, explicit responsibilities, required items
- Tier 2 Ownership & Scale (~30%): architecture, performance, reliability, delivery
- Tier 3 Culture & Values (~20%): collaboration, communication, preferred items

Tier-1 must dominate the summary, top bullets, skills, and opening cover-letter paragraph.

## 2. SUMMARY

Use an executive summary with:
- exact JD title
- total years of experience
- 3-5 Tier-1 technologies/patterns
- 2 quantified impacts
- 1 leadership/collaboration phrase from the JD

## 3. EXPERIENCE

Each bullet must follow:
Strong Verb + Tier-1 Tech/Pattern + System Context + Architectural Depth/Tradeoff + Quantified Outcome

Every bullet must satisfy at least 2 of:
1. Business impact
2. Technical depth
3. Scope/ownership

## 4. SKILLS

Use 4-5 clusters with Tier-1 dominance and exact JD phrasing where possible.

## 5. COVER LETTER

- <=250 words
- JD-specific and non-reusable
- Includes at least one new insight not already stated in the resume

## 6. FINAL QUALITY BAR

The result must feel like a true top-3 submission for THIS JD.
If the impression is only "strong candidate", regenerate internally until it reads like a top-1% submission.

## 7. OUTPUT RULE

Return only the requested document text for this run. Do not include commentary, rationale, or process notes.
"""


DOCX_RENDERING_PROMPT = """Generate a downloadable DOCX resume and cover letter files using the resume and cover letter content that I provide.

CRITICAL OUTPUT RULE
- Output ONLY the downloadable DOCX file.
- Do NOT display the resume text in the chat.
- Do NOT repeat the resume content.
- Do NOT explain formatting decisions.
- The response must contain only the file download.

CRITICAL CONTENT RULE
- Preserve 100% of all bullet points and achievement content exactly as written.
- Do NOT rewrite, paraphrase, summarize, shorten, or optimize wording.
- Do NOT merge or remove bullet points.

You ARE allowed to:
- Remove scope text inside parentheses in job titles.
- Remove short introductory summary sentences directly under job headers.

SECTION ORDER (STRICT)
1. PERSONAL INFO
2. PROFESSIONAL SUMMARY
3. CORE TECHNICAL SKILLS
4. PROFESSIONAL EXPERIENCE
5. EDUCATION

PAGE SETUP
- US Letter, 1-inch margins
- Single-column layout
- ATS-friendly

FONT SYSTEM
- Font: Calibri
- Body: 11 pt
- Line spacing: 1.15

COLOR SYSTEM
- Primary Text Color: Black (#000000)
- Accent Color: Deep Navy (#1F2A44)

PERSONAL INFO
- center aligned
- name 24-26 pt bold accent
- role 16 pt bold black
- contact info 11 pt black

SECTION HEADERS
- 14 pt bold all caps
- accent color

VERB-FOCUSED EMPHASIS
- Bold the first action verb in every bullet
- Bold measurable impact
- Bold only primary stack technologies defining scope
- Target 10-25% bold per bullet
"""


DEFAULT_TEMPLATES = {
    "resume": MASTER_RESUME_ENGINE_PROMPT,
    "cover_letter": MASTER_RESUME_ENGINE_PROMPT,
}


def build_document_generation_prompt(document_type: DocumentType, template: str, job: dict) -> str:
    output_rule = (
        "Output ONLY the ATS-optimized resume in plain text."
        if document_type == DocumentType.RESUME
        else "Output ONLY the JD-tailored cover letter in plain text and keep it at or below 250 words."
    )
    structure_rule = (
        "Structure the resume with these sections in order: PERSONAL INFO, PROFESSIONAL SUMMARY, CORE TECHNICAL SKILLS, PROFESSIONAL EXPERIENCE, EDUCATION."
        if document_type == DocumentType.RESUME
        else "Structure the cover letter as a modern hiring-manager-ready letter with a strong opening, 2 focused body paragraphs, and a concise closing."
    )

    return (
        f"{template}\n\n"
        "FOR THIS REQUEST ONLY\n"
        f"{output_rule}\n"
        f"{structure_rule}\n"
        "Do not include ATS keyword mapping tables or any extra commentary in this run.\n\n"
        "JOB CONTEXT\n"
        f"Title: {job['title']}\n"
        f"Company: {job['company']}\n"
        f"Location: {job.get('location')}\n"
        f"Work mode: {job.get('work_mode')}\n"
        f"Employment type: {job.get('employment_type')}\n"
        f"Short description: {job.get('short_description')}\n\n"
        "FULL JOB DESCRIPTION\n"
        f"{job['description']}\n"
    )


def build_fallback_document(document_type: DocumentType, job: dict) -> str:
    header = "\n".join(
        [
            "Jose Puentes",
            job["title"],
            "Miami, FL | +1 (339) 400 8238",
            "josepuentes0207@gmail.com | LinkedIn",
            "",
        ]
    )

    if document_type == DocumentType.COVER_LETTER:
        return (
            f"{header}"
            f"Dear Hiring Team,\n\n"
            f"I am excited to apply for the {job['title']} role at {job['company']}. "
            f"My background spans full product delivery, platform-minded engineering, and hands-on execution across modern software systems.\n\n"
            f"In roles across Neptie, Acle Law Firm, and PereGonza The Attorneys, I have delivered production software, "
            f"improved internal tooling, and partnered closely with stakeholders to ship reliable features that solve real business problems. "
            f"This opportunity stands out because it combines the technical depth of {job.get('work_mode', 'modern')} engineering with the chance to drive meaningful impact for {job['company']}.\n\n"
            "I would welcome the opportunity to contribute thoughtful engineering execution, strong ownership, and high-quality delivery to your team.\n\n"
            "Sincerely,\n"
            "Jose Puentes"
        )

    return "\n".join(
        [
            header.rstrip(),
            "PROFESSIONAL SUMMARY",
            f"{job['title']} with 7+ years of experience delivering production-ready software, building user-facing applications and backend workflows, and partnering with cross-functional teams to ship reliable features with measurable business impact.",
            "",
            "CORE TECHNICAL SKILLS",
            "Languages & Frameworks: JavaScript, TypeScript, React, Node.js, Python",
            "Platform & Delivery: Docker, CI/CD, REST APIs, PostgreSQL",
            "Engineering Strengths: System design, feature delivery, debugging, cross-functional collaboration",
            "",
            "PROFESSIONAL EXPERIENCE",
            "Neptie - Senior Software Engineer",
            "Miami, FL | May 2022-Present",
            "- Led full-stack feature delivery across production systems, improving release confidence and day-to-day engineering velocity.",
            f"- Built and maintained software aligned to roles like {job['title']}, partnering with stakeholders to translate requirements into shipped functionality.",
            "- Improved maintainability and delivery quality through pragmatic architecture decisions, debugging discipline, and ownership across implementation details.",
            "",
            "Acle Law Firm - Senior Software Engineer",
            "Miami, FL | May 2020-Feb 2022",
            "- Delivered internal platform features and workflow improvements that increased operational efficiency for end users and business teams.",
            "- Built reliable software components, data flows, and user-facing experiences with a focus on usability and long-term maintainability.",
            "",
            "PereGonza The Attorneys - Software Engineer",
            "Miami, FL | Oct 2018-Mar 2020",
            "- Developed production software and internal tooling to support client services and team productivity.",
            "- Collaborated across functional stakeholders to implement features, resolve issues, and improve delivery outcomes.",
            "",
            "EDUCATION",
            "Bachelor of Science in Computer Science",
            "Florida International University | Miami, FL",
        ]
    )


def build_docx_render_prompt(document_type: DocumentType, content: str) -> str:
    document_label = "resume" if document_type == DocumentType.RESUME else "cover letter"
    return (
        f"{DOCX_RENDERING_PROMPT}\n\n"
        "SYSTEM OVERRIDE FOR THIS PIPELINE\n"
        "You are preparing structured text that will be rendered into a DOCX by an external document builder.\n"
        f"Preserve all wording exactly as written for this {document_label}.\n"
        "Return only clean structured plain text for the renderer.\n"
        "Do not add commentary, markdown fences, or notes.\n\n"
        "SOURCE CONTENT TO RENDER\n"
        f"{content}\n"
    )

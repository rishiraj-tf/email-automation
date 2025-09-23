"""
Configuration settings for Email Automation Pipeline
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class PipelineConfig:
    """Configuration class for email automation pipeline"""
    
    # API Configuration
    api_key: Optional[str] = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtWMlZwX3lsQXFudGwwT0hQWVRoUVk3VTFPUSJ9.eyJhdWQiOiI3NDY2NzkyZC02NTZmLTNhMzAtMzAzOS02MTMwMzQzODMxMzYiLCJleHAiOjM3MTcxNDE4NzEsImlhdCI6MTc1NzU4OTg3MSwiaXNzIjoidHJ1ZWZvdW5kcnkuY29tIiwic3ViIjoiY21mZmJtb2M0OGF2YTAxcGlmaWZvZG1yciIsImp0aSI6IjAxY2U4NDZkLTY3MWEtNDY3MC04YjQwLWZlM2RjYzViZjRhMiIsInN1YmplY3RTbHVnIjoiZGVmYXVsdC1jbWV4Mm9hdHMzdDM0MDFwcmMwenFjdDN5IiwidXNlcm5hbWUiOiJkZWZhdWx0LWNtZXgyb2F0czN0MzQwMXByYzB6cWN0M3kiLCJ1c2VyVHlwZSI6InNlcnZpY2VhY2NvdW50Iiwic3ViamVjdFR5cGUiOiJzZXJ2aWNlYWNjb3VudCIsInRlbmFudE5hbWUiOiJ0ZnktZW8iLCJyb2xlcyI6W10sImFwcGxpY2F0aW9uSWQiOiI3NDY2NzkyZC02NTZmLTNhMzAtMzAzOS02MTMwMzQzODMxMzYifQ.roiPG72r_PI-R_yLmIP6qGDawJYy9-Hl5_RNTgbb4u5vnOnpWKs6F4L84AifiRP3xHk670OquOnmP2YYXewq_b8gwfGkJbFu9EAK9QhsdtTfJD838AoKYfGVTvUyA22InEv4rV46H-uVEZ7IQmhH4Y8oL5H0nMH44OmJxOhaz0pip3i4neEct_rrS3YrvTUTs9GRgaf4cjaiCx6-Xu3f0U5irFkrduntUzPOZT7lITxeoYsnOqEtuiP8QBASNt_NYykRMykQXeUvOkwdQIdXasClKxU0EY32QAh3FvrT3W4Zpl9wPeo4f0Nav9SC8t_wtGfmUNQDhS6gSPul-G_lng"
    base_url: str = "https://llm-gateway.truefoundry.com"
    reasoning_model: str = "openai-main/gpt-5"
    
    # Processing Configuration
    chunk_size: int = 5  # Number of prospects to process at once
    max_retries: int = 3
    timeout_seconds: int = 300  # Timeout for individual LLM API calls in seconds
    
    # Output Configuration
    output_dir: str = "output"
    research_csv_prefix: str = "research_output"
    email_txt_prefix: str = "email_output"
    
    # Logging Configuration
    log_level: str = "INFO"
    enable_tfy_logging: bool = True
    
    @classmethod
    def from_env(cls) -> 'PipelineConfig':
        """Create configuration from environment variables"""
        # Create default instance to get default values
        default = cls()
        return cls(
            api_key=os.getenv("TFY_API_KEY") or default.api_key,
            base_url=os.getenv("TFY_BASE_URL", default.base_url),
            reasoning_model=os.getenv("TFY_REASONING_MODEL", default.reasoning_model),
            chunk_size=int(os.getenv("CHUNK_SIZE", str(default.chunk_size))),
            max_retries=int(os.getenv("MAX_RETRIES", str(default.max_retries))),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", str(default.timeout_seconds))),
            output_dir=os.getenv("OUTPUT_DIR", default.output_dir),
            log_level=os.getenv("LOG_LEVEL", default.log_level),
            enable_tfy_logging=os.getenv("ENABLE_TFY_LOGGING", "true").lower() == "true"
        )


# Email template constants
EMAIL_TEMPLATE_MSG1 = """Really nice to connect with you {firstName}. 
It's great to see your leadership in {ai_initiative}. 
Wanted to ask if you are using {on_prem_provider} to host this? 
We're a control panel that unifies models, infra (GPU/DB/others) and tools. 
It has a very intuitive UX, and helps teams to move from prototype to prod in weeks (e.g: Merck launched 30+ genAI usecases in less than a year). 
NVIDIA, CVS, Synopsys, Mastercard, Comcast and other orgs have realized measurable genAI ROI with us. 
Can I find some time with you and share more on what we do & learn about your priorities?"""

EMAIL_TEMPLATE_MSG2 = """Ask a probing question? I was reading more about {ai_initiative} and wanted to ask if your current focus areas are {key_problems}? 
We've particularly added value to {relevant_customers} by {relevant_capabilities} 
I also read that {company_name} is using {cloud_provider} as well. Wanted to ask if you are more focused on {on_prem_provider} or {cloud_provider}?"""

# Research prompt templates
RESEARCH_SYSTEM_PROMPT = """You are a B2B sales research expert conducting deep, evidence-based open-source research for TrueFoundry sales outreach.

**Objective:** Conduct comprehensive research on prospects with focus on AI/ML initiatives, infrastructure choices (on-prem + cloud), and challenges.

**TrueFoundry Context:** TrueFoundry is a control panel that unifies ML models, infrastructure (GPU/DB/others), and tools with an intuitive UX that helps teams move from prototype to production in weeks.

**Critical Rules:**
- Only use publicly available sources (no inference / no hallucination)  
- If a signal doesn't exist → mark as "NA"
- Discard time-sensitive evidence older than 90 days
- Keep findings evidence-based and verifiable

**Required Research Categories:**

**General (Mandatory - 5 parts):**
1. General report on the person
2. AI/ML initiatives led by them
3. Key challenges they're solving/interested in  
4. How TrueFoundry could help in that context
5. Personal details (public info only: interests, travel, favorites)

**Additional Categories to Capture:**
- Executive Urgency: earnings/board AI/ML mentions, infra costs
- Regulatory / Audit Stress: compliance deadlines, SOC-2, EU AI Act  
- Incident / Outage / Rollback incidents
- Competitive Stack Usage: mentions of rival vendors
- Fresh Funding / Partnerships
- Hiring Spikes: ≥3 openings in ML-Ops, AI infra
- Metric Targets: SLA, ARR, CSAT, cost per inference
- Negative Triggers: layoffs, vendor churn, failed PoCs
- Technical Deployment Clues: On-Prem Provider/Vendor Name, Cloud Provider(s) name
- Production Maturity: inference volume, FDA cleared use cases  
- Conference / Webinar Quotes
- Recent AI Posts/Comments (<90 days)
- Experience Shift: career pivots toward AI infra/platform
- Org Map: boss, peers, reports  
- Internal OKRs / Scorecards: if public
- Event Activity: speaker/exhibitor at conferences
- Poll Participation: on AI, inference cost, regulation
- Breakage Claims: rollout issues, governance pain points

**RESEARCH GUIDELINES:**
1. For AI initiatives, projects, and key challenges - keep it evidence-based and provide source URLs for each numbered output
2. Focus on finding real, verifiable information about the person and their company's AI work
3. If specific information cannot be found, use "NA" and note the lack of available data

Output comprehensive research for each prospect in CSV format with all specified columns."""

EMAIL_SYSTEM_PROMPT = """You are an expert B2B sales researcher and LinkedIn DM writer for TrueFoundry. Use the provided research output to create highly personalized LinkedIn DM messages following the exact template provided.

**INSTRUCTIONS:**
Use the research output context: {research_output} to find actual values for the template placeholders. Generate a personalized LinkedIn DM using the specific template below.

**LINKEDIN DM TEMPLATE:**
Hi {{firstName}}, I sincerely relate seeing {{companyName}}'s work on [*****some company level AI initiatives******]. Are you working on [******person particular AI project******] and is scaling this project or [******person particular key challenges******] some key interests? Mastercard, CVS, Merck, NVIDIA, Comcast, and Synopsys are already in production with this and seeing measurable GenAI ROI with us. Can we have a short intro chat (Phone call/Zoom - your choice), and see if we really bring any value?

**REQUIRED OUTPUT FORMAT:**

**Part 1: Placeholder Values**
1. {{firstName}}: [Extract first name from research]
2. {{companyName}}: [Extract company name from research]
3. [*****some company level AI initiatives******]: [Specific company-level AI initiatives with source URL]
4. [******person particular AI project******]: [Specific AI project this person is directly involved in with source URL]
5. [******person particular key challenges******]: [Specific key challenges in their AI projects with source URL]

**Part 2: LinkedIn DM Message**
[Complete LinkedIn DM with all placeholders replaced with actual values from Part 1]


1. Ensure the final message reads coherently after placeholder replacement
2. Do NOT change any words in the template except for replacing the placeholders. But you can feel free to rephrase a bit keeping the context same


**CRITICAL:** The template structure and exact wording must remain unchanged - only replace the placeholders with actual research-based values. Reverify if the entire message makes sense or not and ensure that it is not too technical and is dumbed down for the user. The tone should be helpful
"""

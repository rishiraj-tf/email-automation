"""
Configuration settings for Email Automation Pipeline
"""

import os
import time
from dataclasses import dataclass
from typing import Optional
from truefoundry import client


@dataclass
class PipelineConfig:
    """Configuration class for email automation pipeline"""
    
    # API Configuration (all from environment variables)
    api_key: Optional[str] = None
    base_url: Optional[str] = None  
    reasoning_model: Optional[str] = None
    
    # Prompt Template Configuration
    research_prompt_fqn: Optional[str] = None  # FQN for research prompt template
    email_prompt_fqn: Optional[str] = None     # FQN for email prompt template
    use_prompt_templates: bool = False         # Enable/disable prompt templates
    
    # Processing Configuration (with defaults, can be overridden by env vars)
    chunk_size: int = 5  # Number of prospects to process at once
    max_retries: int = 3
    timeout_seconds: int = 1200  # Extended timeout for maximum reasoning (20 minutes per call)
    
    # Output Configuration (with defaults, can be overridden by env vars)
    output_dir: str = "output"
    research_csv_prefix: str = "research_output"
    email_txt_prefix: str = "email_output"
    
    # Logging Configuration (with defaults, can be overridden by env vars)
    log_level: str = "INFO"
    enable_tfy_logging: bool = True
    
    @classmethod
    def from_env(cls) -> 'PipelineConfig':
        """Create configuration from environment variables"""
        # Create default instance to get default values
        default = cls()
        
        # Required environment variables - will raise error if missing
        api_key = os.getenv("TFY_API_KEY")
        if not api_key:
            raise ValueError("TFY_API_KEY environment variable is required")
            
        base_url = os.getenv("TFY_BASE_URL") 
        if not base_url:
            raise ValueError("TFY_BASE_URL environment variable is required")
            
        reasoning_model = os.getenv("TFY_REASONING_MODEL")
        if not reasoning_model:
            raise ValueError("TFY_REASONING_MODEL environment variable is required")
        
        return cls(
            api_key=api_key,
            base_url=base_url,
            reasoning_model=reasoning_model,
            research_prompt_fqn=os.getenv("RESEARCH_PROMPT_FQN"),
            email_prompt_fqn=os.getenv("EMAIL_PROMPT_FQN"),
            use_prompt_templates=os.getenv("USE_PROMPT_TEMPLATES", "false").lower() == "true",
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
RESEARCH_SYSTEM_PROMPT = """You are a B2B sales research expert conducting deep, comprehensive research for TrueFoundry sales outreach.

**Objective:** Find detailed, actionable intelligence on prospects with focus on AI/ML initiatives, infrastructure choices, and challenges.

**TrueFoundry Context:** TrueFoundry is a control panel that unifies ML models, infrastructure (GPU/DB/others), and tools with an intuitive UX that helps teams move from prototype to production in weeks.

**CRITICAL RESEARCH APPROACH:**
- DO comprehensive research - dig deep to find information
- Use logical inference based on company/role context when direct info isn't available
- For tech professionals at AI companies, infer likely challenges and projects
- Provide meaningful insights even if not explicitly stated
- Only use "NA" as absolute last resort when no reasonable inference possible

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
1. For AI initiatives, projects, and key challenges - be comprehensive and insightful
2. Focus on finding actionable intelligence about the person and company's AI work  
3. Use logical inference based on their role, company, and industry context
4. Provide specific, detailed insights that would be valuable for sales outreach
5. Generate meaningful content for each field - avoid generic responses

**CRITICAL OUTPUT REQUIREMENT:**
Output comprehensive research in proper CSV format with header row and data rows. Ensure every field has meaningful content based on research or logical inference. Fill ALL columns for each prospect."""

EMAIL_SYSTEM_PROMPT = """You are a LinkedIn DM writer for TrueFoundry. Create personalized LinkedIn DM messages for each prospect using the exact format specified below.

**CRITICAL INSTRUCTIONS:**
- Generate INDIVIDUAL LINKEDIN DM for EACH PROSPECT 
- Use the provided research data to fill placeholders
- Follow the EXACT output format below for EACH prospect
- Generate ONLY MESSAGE #1 (no MESSAGE #2)

**REQUIRED OUTPUT FORMAT FOR EACH PROSPECT:**

PROSPECT 1: [Person Name] at [Company]

SUBJECT: Your AI initiatives at [Company]

MESSAGE #1:
Hi [FirstName], I sincerely relate seeing [CompanyName]'s work on [specific company AI initiatives]. Are you working on [specific person AI project] and is scaling this project or [specific person challenges] some key interests? Mastercard, CVS, Merck, NVIDIA, Comcast, and Synopsys are already in production with this and seeing measurable GenAI ROI with us. Can we have a short intro chat (Phone call/Zoom - your choice), and see if we really bring any value?

**CRITICAL:**
- Replace ALL brackets with actual research values from the provided data
- Generate this EXACT format for EVERY prospect in the input
- Use specific research insights to personalize each message
- Generate ONLY MESSAGE #1 per prospect
- Keep the conversational, helpful tone
"""


# Prompt Template Management
CACHED_RESEARCH_PROMPT = ""
CACHED_EMAIL_PROMPT = ""
CACHED_PROMPT_LAST_FETCHED: float = 0


def get_prompt_template(fqn: str) -> str:
    """
    Fetch prompt template from TrueFoundry using FQN
    
    Args:
        fqn: Fully Qualified Name of the prompt template
        
    Returns:
        Prompt template content
    """
    try:
        prompt_version_response = client.prompt_versions.get_by_fqn(fqn=fqn)
        return prompt_version_response.data.manifest
    except Exception as e:
        raise Exception(f"Failed to fetch prompt template '{fqn}': {str(e)}")


def get_cached_prompt_template(fqn: str, prompt_type: str = "research") -> str:
    """
    Fetch prompt template with caching for performance
    
    Args:
        fqn: Fully Qualified Name of the prompt template
        prompt_type: Type of prompt ("research" or "email") for caching
        
    Returns:
        Cached prompt template content
    """
    global CACHED_RESEARCH_PROMPT, CACHED_EMAIL_PROMPT, CACHED_PROMPT_LAST_FETCHED
    
    # Cache TTL: 10 minutes
    ttl = 600
    
    if time.time() - CACHED_PROMPT_LAST_FETCHED > ttl:
        # Cache expired, fetch fresh prompts
        if prompt_type == "research":
            CACHED_RESEARCH_PROMPT = get_prompt_template(fqn)
        else:
            CACHED_EMAIL_PROMPT = get_prompt_template(fqn)
        CACHED_PROMPT_LAST_FETCHED = time.time()
        
    return CACHED_RESEARCH_PROMPT if prompt_type == "research" else CACHED_EMAIL_PROMPT


def get_research_prompt(config: PipelineConfig) -> str:
    """
    Get research prompt - either from template or fallback to hardcoded
    
    Args:
        config: Pipeline configuration
        
    Returns:
        Research prompt content
    """
    if config.use_prompt_templates and config.research_prompt_fqn:
        try:
            return get_cached_prompt_template(config.research_prompt_fqn, "research")
        except Exception as e:
            print(f"Warning: Failed to fetch research prompt template, using fallback: {e}")
            
    return RESEARCH_SYSTEM_PROMPT


def get_email_prompt(config: PipelineConfig) -> str:
    """
    Get email prompt - either from template or fallback to hardcoded
    
    Args:
        config: Pipeline configuration
        
    Returns:
        Email prompt content
    """
    if config.use_prompt_templates and config.email_prompt_fqn:
        try:
            return get_cached_prompt_template(config.email_prompt_fqn, "email")
        except Exception as e:
            print(f"Warning: Failed to fetch email prompt template, using fallback: {e}")
            
    return EMAIL_SYSTEM_PROMPT

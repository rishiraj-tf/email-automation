"""
Sales Email Automation Backend
Processes prospect CSV files through research and email generation pipeline
"""

import csv
import json
import logging
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from openai import OpenAI

from config import PipelineConfig, RESEARCH_SYSTEM_PROMPT, EMAIL_SYSTEM_PROMPT, get_research_prompt, get_email_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProspectInput:
    """Input data structure for prospects from CSV"""
    person_name: str
    company_name: str
    linkedin_url: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProspectInput':
        return cls(**data)


@dataclass
class ResearchOutput:
    """Output data structure for comprehensive research results"""
    person_name: str
    company_name: str
    linkedin_url: str
    
    # General Section (Mandatory - 5 parts)
    general_report: str
    ai_ml_initiatives: str
    key_challenges_solving: str
    how_truefoundry_can_help: str
    personal_details: str
    
    # Executive Urgency
    executive_urgency_earnings_board_mentions: str
    executive_urgency_infra_costs: str
    
    # Regulatory / Audit Stress
    regulatory_compliance_deadlines: str
    regulatory_soc2_eu_ai_act: str
    
    # Incident / Outage / Rollback
    incident_outage_rollback: str
    
    # Competitive Stack Usage
    competitive_stack_usage_rival_vendors: str
    
    # Fresh Funding / Partnerships
    fresh_funding_partnerships: str
    
    # Hiring Spikes
    hiring_spikes_ml_ops_ai_infra: str
    
    # Metric Targets
    metric_targets_sla_arr_csat_cost: str
    
    # Negative Triggers
    negative_triggers_layoffs_churn_failed_pocs: str
    
    # Technical Deployment Clues
    technical_deployment_on_prem_provider: str
    technical_deployment_cloud_providers: str
    
    # Production Maturity
    production_maturity_inference_volume: str
    production_maturity_fda_cleared: str
    
    # Conference / Webinar Quotes
    conference_webinar_quotes: str
    
    # Recent AI Posts/Comments
    recent_ai_posts_comments_90_days: str
    
    # Experience Shift
    experience_shift_career_pivot: str
    
    # Org Map
    org_map_boss_peers_reports: str
    
    # Internal OKRs / Scorecards
    internal_okrs_scorecards: str
    
    # Event Activity
    event_activity_speaker_exhibitor: str
    
    # Poll Participation
    poll_participation_ai_cost_regulation: str
    
    # Breakage Claims
    breakage_claims_rollout_governance: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def get_csv_headers(cls) -> List[str]:
        """Get CSV headers for output file"""
        return [
            'person_name', 'company_name', 'linkedin_url',
            # General Section
            'general_report', 'ai_ml_initiatives', 'key_challenges_solving',
            'how_truefoundry_can_help', 'personal_details',
            # Executive Urgency
            'executive_urgency_earnings_board_mentions', 'executive_urgency_infra_costs',
            # Regulatory
            'regulatory_compliance_deadlines', 'regulatory_soc2_eu_ai_act',
            # Incident
            'incident_outage_rollback',
            # Competitive
            'competitive_stack_usage_rival_vendors',
            # Funding
            'fresh_funding_partnerships',
            # Hiring
            'hiring_spikes_ml_ops_ai_infra',
            # Metrics
            'metric_targets_sla_arr_csat_cost',
            # Negative Triggers
            'negative_triggers_layoffs_churn_failed_pocs',
            # Technical
            'technical_deployment_on_prem_provider', 'technical_deployment_cloud_providers',
            # Production
            'production_maturity_inference_volume', 'production_maturity_fda_cleared',
            # Conference
            'conference_webinar_quotes',
            # Recent Posts
            'recent_ai_posts_comments_90_days',
            # Experience
            'experience_shift_career_pivot',
            # Org
            'org_map_boss_peers_reports',
            # OKRs
            'internal_okrs_scorecards',
            # Events
            'event_activity_speaker_exhibitor',
            # Polls
            'poll_participation_ai_cost_regulation',
            # Breakage
            'breakage_claims_rollout_governance'
        ]
    
    def to_markdown_table_row(self) -> str:
        """Convert research output to markdown table format"""
        fields = [
            ("General Report", self.general_report, "Understanding the person and role", "LinkedIn, company bio, recent posts"),
            ("AI/ML Initiatives", self.ai_ml_initiatives, "Active AI projects indicate need for infrastructure", "Company blog, press releases, LinkedIn posts"),
            ("Key Challenges", self.key_challenges_solving, "Pain points TrueFoundry can solve", "Technical posts, interviews, conference talks"),
            ("TrueFoundry Fit", self.how_truefoundry_can_help, "Value proposition alignment", "Analysis of needs vs TrueFoundry capabilities"),
            ("Personal Details", self.personal_details, "Relationship building and personalization", "Social media, interviews, bio information"),
            ("Executive Urgency - Earnings", self.executive_urgency_earnings_board_mentions, "Board pressure creates urgency", "Earnings calls, board reports"),
            ("Executive Urgency - Costs", self.executive_urgency_infra_costs, "Cost pressure drives platform adoption", "Financial reports, cost optimization mentions"),
            ("Regulatory Compliance", self.regulatory_compliance_deadlines, "Compliance creates urgency for governance", "Regulatory filings, compliance mentions"),
            ("SOC-2 / EU AI Act", self.regulatory_soc2_eu_ai_act, "Regulatory requirements drive platform needs", "Compliance documentation, regulatory mentions"),
            ("Incidents/Outages", self.incident_outage_rollback, "System reliability issues indicate infrastructure needs", "Status pages, incident reports, postmortems"),
            ("Competitive Stack", self.competitive_stack_usage_rival_vendors, "Current vendor relationships and switching potential", "Tech stack mentions, vendor discussions"),
            ("Funding/Partnerships", self.fresh_funding_partnerships, "New funding enables new technology adoption", "Funding announcements, partnership news"),
            ("Hiring Spikes", self.hiring_spikes_ml_ops_ai_infra, "Hiring indicates growing AI/ML operations", "Job postings, hiring announcements"),
            ("Metric Targets", self.metric_targets_sla_arr_csat_cost, "Performance targets drive infrastructure decisions", "KPI mentions, performance reports"),
            ("Negative Triggers", self.negative_triggers_layoffs_churn_failed_pocs, "Pain points create openness to alternatives", "News reports, failed project mentions"),
            ("On-Prem Deployment", self.technical_deployment_on_prem_provider, "Current infrastructure choices", "Technical documentation, architecture discussions"),
            ("Cloud Providers", self.technical_deployment_cloud_providers, "Cloud strategy and multi-cloud needs", "Cloud provider mentions, architecture posts"),
            ("Production Scale", self.production_maturity_inference_volume, "Scale indicates serious AI operations", "Performance metrics, volume discussions"),
            ("FDA/Regulated", self.production_maturity_fda_cleared, "Regulated industries need compliant platforms", "Regulatory approvals, compliance mentions"),
            ("Conference Quotes", self.conference_webinar_quotes, "Public statements reveal priorities and challenges", "Conference recordings, webinar content"),
            ("Recent AI Posts", self.recent_ai_posts_comments_90_days, "Current thinking and active engagement", "Social media posts, comments, discussions"),
            ("Experience Shift", self.experience_shift_career_pivot, "Career pivots indicate growing AI focus", "LinkedIn updates, role changes"),
            ("Org Map", self.org_map_boss_peers_reports, "Decision making structure and influence", "Org charts, LinkedIn connections, team pages"),
            ("Internal OKRs", self.internal_okrs_scorecards, "Internal metrics drive technology decisions", "Public OKR mentions, performance discussions"),
            ("Event Activity", self.event_activity_speaker_exhibitor, "Industry engagement indicates influence", "Conference speaker lists, event participation"),
            ("Poll Participation", self.poll_participation_ai_cost_regulation, "Engagement shows active interest in topics", "Social media polls, survey responses"),
            ("Breakage Claims", self.breakage_claims_rollout_governance, "Infrastructure pain points create opportunities", "Problem reports, infrastructure complaints")
        ]
        
        markdown_rows = []
        for category, signal, why_matters, how_to_capture in fields:
            # Use signal value or "NA" if empty/not found
            signal_value = signal if signal and signal.strip() and signal.strip().lower() != "to be filled by llm" else "NA"
            source_url = self.linkedin_url if signal_value != "NA" else "NA"
            
            markdown_rows.append(f"| {category} | {signal_value} | {why_matters} | {how_to_capture} | {signal_value} | {source_url} |")
        
        return "\n".join(markdown_rows)


@dataclass
class EmailOutput:
    """Output data structure for generated emails"""
    person_name: str
    company_name: str
    email_subject: str
    email_body_msg1: str
    email_body_msg2: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TrueFoundryGateway:
    """Gateway class for TrueFoundry LLM API calls"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    
    def call_research_llm(self, prospects: List[ProspectInput]) -> List[ResearchOutput]:
        """
        First LLM call: Convert prospect data to research output
        """
        logger.info(f"Starting research for {len(prospects)} prospects")
        
        # Prepare input data as CSV format string
        csv_input = self._prospects_to_csv_string(prospects)
        
        user_prompt = f"""Conduct focused research on these prospects for LinkedIn DM generation:

Input CSV:
{csv_input}

RESEARCH REQUIREMENTS:
- For each prospect, find their specific AI/ML work and company's AI initiatives  
- Use logical inference based on their role, company, and industry
- Provide detailed, comprehensive insights for each field - be thorough and specific
- Focus on LinkedIn DM essentials + TrueFoundry value proposition

OUTPUT REQUIREMENTS:
Generate detailed JSON with ONLY 6 fields per prospect:

{', '.join([f'"{prospect.person_name} at {prospect.company_name}"' for prospect in prospects])}

CRITICAL: 
1. Output ONLY the 6 fields specified in system prompt
2. Provide rich, detailed content for each field - no length restrictions
3. Generate exactly {len(prospects)} objects
4. Output PERFECT, PARSEABLE JSON ONLY - no markdown, no text, no formatting errors
5. Focus on comprehensive LinkedIn DM personalization + specific TrueFoundry value
6. WARNING: Any JSON formatting errors will cause COMPLETE SYSTEM FAILURE - be precise"""

        try:
            # Get research prompt (either from template or fallback)
            research_prompt = get_research_prompt(self.config)
            
            response = self.client.chat.completions.create(
            messages=[
                    {"role": "system", "content": research_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.config.reasoning_model,
                reasoning_effort="high",  # TrueFoundry supports: low, medium, high
                max_completion_tokens=16000,  # Increased for detailed research responses
                temperature=0.1,   # Low temperature for more focused reasoning
                stream=False,
                timeout=self.config.timeout_seconds,
            extra_headers={
                    "X-TFY-METADATA": '{"service":"sales_automation","step":"research"}',
                    "X-TFY-LOGGING-CONFIG": f'{{"enabled": {str(self.config.enable_tfy_logging).lower()}}}',
                }
            )
            
            # Debug logging
            logger.info(f"Research API call completed successfully")
            if not response.choices:
                logger.error("No choices in API response")
                raise Exception("No choices returned from LLM API")
            
            research_json_content = response.choices[0].message.content
            logger.info(f"Research response length: {len(research_json_content) if research_json_content else 0}")
            logger.info(f"Research response preview: {research_json_content[:500] if research_json_content else 'None'}")
            
            if not research_json_content:
                logger.error("Empty research response content")
                raise Exception("Empty response content from research LLM call")
            
            from parsing_utils import LLMResponseParser
            parser = LLMResponseParser()
            parsed_results = parser.parse_research_json(research_json_content, prospects)
            logger.info(f"Parsed {len(parsed_results)} research results")
            return parsed_results
            
        except Exception as e:
            if "timeout" in str(e).lower():
                logger.error(f"Research LLM call timed out after {self.config.timeout_seconds} seconds: {e}")
                raise Exception(f"LLM API call timed out after {self.config.timeout_seconds} seconds. Try reducing CHUNK_SIZE or increasing TIMEOUT_SECONDS.")
            else:
                logger.error(f"Research LLM call failed: {e}")
                raise
    
    def call_email_llm(self, research_results: List[ResearchOutput]) -> List[EmailOutput]:
        """
        Second LLM call: Convert research data to personalized emails
        """
        logger.info(f"Generating emails for {len(research_results)} prospects")
        
        # Prepare research data as input
        research_input = self._research_to_input_string(research_results)

        user_prompt = f"""Generate personalized LinkedIn DM messages for each prospect using the comprehensive research data below:

{research_input}

CRITICAL INSTRUCTIONS:
1. You MUST generate a UNIQUE message for EACH of the {len(research_results)} prospects above
2. Each message MUST use that specific person's research data (AI initiatives, projects, challenges)
3. DO NOT reuse the same message for multiple people
4. Follow the EXACT output format below

OUTPUT FORMAT REQUIRED:
Generate this format for ALL {len(research_results)} prospects:

PROSPECT 1: [Full Name] at [Company]
SUBJECT: Your AI initiatives at [Company]
MESSAGE #1:
Hi [FirstName], I sincerely relate seeing [Company]'s work on [USE THEIR SPECIFIC AI INITIATIVES FROM RESEARCH]. Are you working on [USE THEIR SPECIFIC AI PROJECT FROM RESEARCH] and is scaling this project or [USE THEIR SPECIFIC CHALLENGES FROM RESEARCH] some key interests? Mastercard, CVS, Merck, NVIDIA, Comcast, and Synopsys are already in production with this and seeing measurable GenAI ROI with us. Can we have a short intro chat (Phone call/Zoom - your choice), and see if we really bring any value?

[Repeat for PROSPECT 2, PROSPECT 3, etc. with THEIR SPECIFIC research data]

VERIFICATION: You must generate {len(research_results)} different messages total."""

        try:
            # Get email prompt (either from template or fallback)
            email_prompt = get_email_prompt(self.config)
            
            response = self.client.chat.completions.create(
            messages=[
                    {"role": "system", "content": email_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.config.reasoning_model,
                reasoning_effort="high",  # TrueFoundry supports: low, medium, high
                max_completion_tokens=16000,  # Increased for detailed research responses
                temperature=0.1,   # Low temperature for more focused reasoning
                stream=False,
                timeout=self.config.timeout_seconds,
                extra_headers={
                    "X-TFY-METADATA": '{"service":"sales_automation","step":"email_generation"}',
                    "X-TFY-LOGGING-CONFIG": f'{{"enabled": {str(self.config.enable_tfy_logging).lower()}}}',
                }
            )
            
            # Debug logging
            logger.info(f"Email API call completed successfully")
            if not response.choices:
                logger.error("No choices in email API response")
                raise Exception("No choices returned from email LLM API")
            
            email_content = response.choices[0].message.content
            logger.info(f"Email response length: {len(email_content) if email_content else 0}")
            logger.info(f"Email response preview: {email_content[:500] if email_content else 'None'}")
            
            if not email_content:
                logger.error("Empty email response content")
                raise Exception("Empty response content from email LLM call")
            
            from parsing_utils import LLMResponseParser
            parser = LLMResponseParser()
            parsed_emails = parser.parse_email_response(email_content, research_results)
            logger.info(f"Parsed {len(parsed_emails)} email results")
            return parsed_emails
            
        except Exception as e:
            if "timeout" in str(e).lower():
                logger.error(f"Email LLM call timed out after {self.config.timeout_seconds} seconds: {e}")
                raise Exception(f"LLM API call timed out after {self.config.timeout_seconds} seconds. Try reducing CHUNK_SIZE or increasing TIMEOUT_SECONDS.")
            else:
                logger.error(f"Email LLM call failed: {e}")
                raise
    
    def _prospects_to_csv_string(self, prospects: List[ProspectInput]) -> str:
        """Convert prospects to CSV string format"""
        output = "person_name,company_name,linkedin_url\n"
        for prospect in prospects:
            output += f'"{prospect.person_name}","{prospect.company_name}","{prospect.linkedin_url}"\n'
        return output
    
    def _research_to_input_string(self, research_results: List[ResearchOutput]) -> str:
        """Convert research results to structured input for email generation"""
        output = ""
        for i, result in enumerate(research_results, 1):
            output += f"""
PROSPECT {i}: {result.person_name} at {result.company_name}

RESEARCH DATA:
- First Name: {result.person_name.split()[0]}
- Company: {result.company_name}
- LinkedIn: {result.linkedin_url}
- Company AI Initiatives: {result.ai_ml_initiatives}
- Person's Specific AI Project: {result.general_report}
- Person's Key Challenges: {result.key_challenges_solving}
- Technical Stack: On-Prem: {result.technical_deployment_on_prem_provider}, Cloud: {result.technical_deployment_cloud_providers}
- How TrueFoundry Helps: {result.how_truefoundry_can_help}

CRITICAL: Use THIS SPECIFIC research data above to personalize the LinkedIn DM for {result.person_name}. Each message must be unique based on their specific AI initiatives and challenges.

---
"""
        return output
    
    # Parsing methods have been moved to LLMResponseParser class
    


class EmailAutomationPipeline:
    """Main orchestration class for the email automation pipeline"""
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig.from_env()
        self.gateway = TrueFoundryGateway(self.config)
    
    def process_csv_file(self, input_csv_path: str, output_dir: str = "output") -> Dict[str, str]:
        """
        Main processing function - reads CSV, processes through pipeline, outputs results
        
        Args:
            input_csv_path: Path to input CSV file
            output_dir: Directory to save output files
            
        Returns:
            Dictionary with paths to output files
        """
        logger.info(f"Starting email automation pipeline for {input_csv_path}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Read and validate input CSV
            prospects = self._read_csv_file(input_csv_path)
            logger.info(f"Loaded {len(prospects)} prospects from CSV")
            
            # Process in chunks to manage token limits
            all_research_results = []
            all_email_results = []
            
            for i in range(0, len(prospects), self.config.chunk_size):
                chunk = prospects[i:i + self.config.chunk_size]
                logger.info(f"Processing chunk {i//self.config.chunk_size + 1}: prospects {i+1}-{min(i+self.config.chunk_size, len(prospects))}")
                
                # Research phase
                research_results = self.gateway.call_research_llm(chunk)
                all_research_results.extend(research_results)
                
                # Email generation phase
                email_results = self.gateway.call_email_llm(research_results)
                all_email_results.extend(email_results)
            
            # Generate output files
            research_csv_path = os.path.join(output_dir, f"research_output_{timestamp}.csv")
            research_md_path = os.path.join(output_dir, f"research_output_{timestamp}.md")
            email_txt_path = os.path.join(output_dir, f"email_output_{timestamp}.txt")
            
            self._save_research_csv(all_research_results, research_csv_path)
            self._save_research_markdown(all_research_results, research_md_path)
            self._save_email_txt(all_email_results, email_txt_path)
            
            logger.info("Pipeline completed successfully")
            return {
                "research_csv": research_csv_path,
                "research_md": research_md_path,
                "email_txt": email_txt_path,
                "total_prospects": len(prospects)
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
    
    def _read_csv_file(self, csv_path: str) -> List[ProspectInput]:
        """Read and validate CSV file"""
        prospects = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate headers
                expected_headers = {'person_name', 'company_name', 'linkedin_url'}
                if not expected_headers.issubset(set(reader.fieldnames)):
                    raise ValueError(f"CSV must contain columns: {expected_headers}")
                
                for row in reader:
                    # Validate required fields
                    if not all(row.get(field, '').strip() for field in expected_headers):
                        logger.warning(f"Skipping incomplete row: {row}")
                        continue
                    
                    prospect = ProspectInput(
                        person_name=row['person_name'].strip(),
                        company_name=row['company_name'].strip(),
                        linkedin_url=row['linkedin_url'].strip()
                    )
                    prospects.append(prospect)
                    
        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}")
            raise
            
        if not prospects:
            raise ValueError("No valid prospects found in CSV file")
            
        return prospects
    
    def _save_research_csv(self, research_results: List[ResearchOutput], output_path: str):
        """Save research results to CSV file"""
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=ResearchOutput.get_csv_headers())
            writer.writeheader()
            
            for result in research_results:
                writer.writerow(result.to_dict())
        
        logger.info(f"Research CSV saved to {output_path}")
    
    def _save_research_markdown(self, research_results: List[ResearchOutput], output_path: str):
        """Save research results to Markdown table format"""
        with open(output_path, 'w', encoding='utf-8') as file:
            # Write markdown table header
            file.write("# Sales Research Results\n\n")
            file.write("| Category Signal | Why it matters (sales-use lens) | How to capture (open-source clues) | Signal Description | Source URL Evidence |\n")
            file.write("|---|---|---|---|---|\n")
            
            # Write research data for each prospect
            for i, result in enumerate(research_results, 1):
                file.write(f"\n## Prospect {i}: {result.person_name} at {result.company_name}\n\n")
                file.write(result.to_markdown_table_row())
                file.write("\n")
        
        logger.info(f"Research Markdown saved to {output_path}")
    
    def _save_email_txt(self, email_results: List[EmailOutput], output_path: str):
        """Save email results to text file"""
        with open(output_path, 'w', encoding='utf-8') as file:
            for i, email in enumerate(email_results, 1):
                file.write(f"{'='*60}\n")
                file.write(f"EMAIL {i}: {email.person_name} at {email.company_name}\n")
                file.write(f"{'='*60}\n\n")
                
                file.write(f"SUBJECT: {email.email_subject}\n\n")
                
                file.write("MESSAGE #1:\n")
                file.write("-" * 40 + "\n")
                file.write(f"{email.email_body_msg1}\n\n")
                
                file.write("MESSAGE #2:\n")
                file.write("-" * 40 + "\n")
                file.write(f"{email.email_body_msg2}\n\n")
        
        logger.info(f"Email text file saved to {output_path}")


def main():
    """Example usage of the email automation pipeline"""
    # Initialize pipeline with configuration
    config = PipelineConfig.from_env()
    pipeline = EmailAutomationPipeline(config)
    
    # Process CSV file
    input_file = "karl_martin_prospect.csv"  # Example with Karl Martin
    
    try:
        results = pipeline.process_csv_file(input_file)
        print(f"Pipeline completed successfully!")
        print(f"Research CSV: {results['research_csv']}")
        print(f"Research Markdown: {results['research_md']}")
        print(f"Email output: {results['email_txt']}")
        print(f"Processed {results['total_prospects']} prospects")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")


if __name__ == "__main__":
    main()

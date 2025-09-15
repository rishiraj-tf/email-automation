"""
Parsing utilities for LLM responses
"""

import csv
import re
import logging
from typing import List, Dict, Any
from io import StringIO

logger = logging.getLogger(__name__)


class LLMResponseParser:
    """Parser for LLM responses in different formats"""
    
    @staticmethod
    def parse_research_csv(csv_content: str, original_prospects: List):
        """
        Parse research CSV content from LLM response
        
        Args:
            csv_content: Raw CSV content from LLM
            original_prospects: Original prospect data for fallback
            
        Returns:
            List of ResearchOutput objects
        """
        from email_automation import ResearchOutput
        results = []
        
        try:
            # Clean the CSV content
            cleaned_content = LLMResponseParser._clean_csv_content(csv_content)
            
            # Parse CSV
            csv_file = StringIO(cleaned_content)
            reader = csv.DictReader(csv_file)
            
            parsed_rows = list(reader)
            
            # Match with original prospects and create ResearchOutput objects
            for i, prospect in enumerate(original_prospects):
                if i < len(parsed_rows):
                    row = parsed_rows[i]
                    result = LLMResponseParser._create_research_output(row, prospect)
                else:
                    # Create fallback result if parsing fails
                    result = LLMResponseParser._create_fallback_research_output(prospect)
                
                results.append(result)
                
        except Exception as e:
            logger.warning(f"Failed to parse research CSV: {e}. Using fallback parsing.")
            
            # Fallback: Create basic research outputs
            for prospect in original_prospects:
                result = LLMResponseParser._create_fallback_research_output(prospect)
                results.append(result)
        
        return results
    
    @staticmethod
    def parse_email_response(email_content: str, research_results: List):
        """
        Parse email content from LLM response
        
        Args:
            email_content: Raw email content from LLM
            research_results: Research results for context
            
        Returns:
            List of EmailOutput objects
        """
        from email_automation import EmailOutput
        emails = []
        
        try:
            # Split content by email sections
            email_sections = LLMResponseParser._split_email_content(email_content)
            
            for i, research in enumerate(research_results):
                if i < len(email_sections):
                    section = email_sections[i]
                    email = LLMResponseParser._parse_email_section(section, research)
                else:
                    # Create fallback email
                    email = LLMResponseParser._create_fallback_email(research)
                
                emails.append(email)
                
        except Exception as e:
            logger.warning(f"Failed to parse email content: {e}. Using fallback parsing.")
            
            # Fallback: Create basic emails
            for research in research_results:
                email = LLMResponseParser._create_fallback_email(research)
                emails.append(email)
        
        return emails
    
    @staticmethod
    def _clean_csv_content(csv_content: str) -> str:
        """Clean CSV content from LLM response"""
        # Remove markdown code blocks
        csv_content = re.sub(r'```csv\n?', '', csv_content)
        csv_content = re.sub(r'```\n?', '', csv_content)
        
        # Remove extra explanatory text
        lines = csv_content.split('\n')
        csv_lines = []
        header_found = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for CSV header
            if 'person_name' in line.lower() and 'company_name' in line.lower():
                header_found = True
                csv_lines.append(line)
            elif header_found and (',' in line or '"' in line):
                csv_lines.append(line)
        
        return '\n'.join(csv_lines)
    
    @staticmethod
    def _create_research_output(row: Dict[str, Any], prospect):
        """Create ResearchOutput from parsed CSV row"""
        from email_automation import ResearchOutput
        return ResearchOutput(
            person_name=row.get('person_name', prospect.person_name),
            company_name=row.get('company_name', prospect.company_name),
            linkedin_url=row.get('linkedin_url', prospect.linkedin_url),
            
            # General Section
            general_report=row.get('general_report', 'To be researched'),
            ai_ml_initiatives=row.get('ai_ml_initiatives', 'AI initiatives to be researched'),
            key_challenges_solving=row.get('key_challenges_solving', 'Technical challenges to be identified'),
            how_truefoundry_can_help=row.get('how_truefoundry_can_help', 'Infrastructure unification and MLOps'),
            personal_details=row.get('personal_details', 'Professional interests to be researched'),
            
            # Executive Urgency
            executive_urgency_earnings_board_mentions=row.get('executive_urgency_earnings_board_mentions', 'NA'),
            executive_urgency_infra_costs=row.get('executive_urgency_infra_costs', 'NA'),
            
            # Regulatory
            regulatory_compliance_deadlines=row.get('regulatory_compliance_deadlines', 'NA'),
            regulatory_soc2_eu_ai_act=row.get('regulatory_soc2_eu_ai_act', 'NA'),
            
            # Incident
            incident_outage_rollback=row.get('incident_outage_rollback', 'NA'),
            
            # Competitive
            competitive_stack_usage_rival_vendors=row.get('competitive_stack_usage_rival_vendors', 'NA'),
            
            # Funding
            fresh_funding_partnerships=row.get('fresh_funding_partnerships', 'NA'),
            
            # Hiring
            hiring_spikes_ml_ops_ai_infra=row.get('hiring_spikes_ml_ops_ai_infra', 'NA'),
            
            # Metrics
            metric_targets_sla_arr_csat_cost=row.get('metric_targets_sla_arr_csat_cost', 'NA'),
            
            # Negative Triggers
            negative_triggers_layoffs_churn_failed_pocs=row.get('negative_triggers_layoffs_churn_failed_pocs', 'NA'),
            
            # Technical
            technical_deployment_on_prem_provider=row.get('technical_deployment_on_prem_provider', 'NA'),
            technical_deployment_cloud_providers=row.get('technical_deployment_cloud_providers', 'NA'),
            
            # Production
            production_maturity_inference_volume=row.get('production_maturity_inference_volume', 'NA'),
            production_maturity_fda_cleared=row.get('production_maturity_fda_cleared', 'NA'),
            
            # Conference
            conference_webinar_quotes=row.get('conference_webinar_quotes', 'NA'),
            
            # Recent Posts
            recent_ai_posts_comments_90_days=row.get('recent_ai_posts_comments_90_days', 'NA'),
            
            # Experience
            experience_shift_career_pivot=row.get('experience_shift_career_pivot', 'NA'),
            
            # Org
            org_map_boss_peers_reports=row.get('org_map_boss_peers_reports', 'NA'),
            
            # OKRs
            internal_okrs_scorecards=row.get('internal_okrs_scorecards', 'NA'),
            
            # Events
            event_activity_speaker_exhibitor=row.get('event_activity_speaker_exhibitor', 'NA'),
            
            # Polls
            poll_participation_ai_cost_regulation=row.get('poll_participation_ai_cost_regulation', 'NA'),
            
            # Breakage
            breakage_claims_rollout_governance=row.get('breakage_claims_rollout_governance', 'NA')
        )
    
    @staticmethod
    def _create_fallback_research_output(prospect):
        """Create fallback ResearchOutput when parsing fails"""
        from email_automation import ResearchOutput
        return ResearchOutput(
            person_name=prospect.person_name,
            company_name=prospect.company_name,
            linkedin_url=prospect.linkedin_url,
            
            # General Section
            general_report="AI/ML professional to be researched further",
            ai_ml_initiatives="AI/ML initiatives to be researched further",
            key_challenges_solving="Infrastructure scaling and MLOps challenges",
            how_truefoundry_can_help="Unified ML platform for faster deployment",
            personal_details="Professional interests in AI/ML space",
            
            # Executive Urgency  
            executive_urgency_earnings_board_mentions="NA",
            executive_urgency_infra_costs="NA",
            
            # Regulatory
            regulatory_compliance_deadlines="NA",
            regulatory_soc2_eu_ai_act="NA",
            
            # Incident
            incident_outage_rollback="NA",
            
            # Competitive
            competitive_stack_usage_rival_vendors="NA",
            
            # Funding
            fresh_funding_partnerships="NA",
            
            # Hiring
            hiring_spikes_ml_ops_ai_infra="NA",
            
            # Metrics
            metric_targets_sla_arr_csat_cost="NA",
            
            # Negative Triggers
            negative_triggers_layoffs_churn_failed_pocs="NA",
            
            # Technical
            technical_deployment_on_prem_provider="NA",
            technical_deployment_cloud_providers="NA",
            
            # Production
            production_maturity_inference_volume="NA",
            production_maturity_fda_cleared="NA",
            
            # Conference
            conference_webinar_quotes="NA",
            
            # Recent Posts
            recent_ai_posts_comments_90_days="NA",
            
            # Experience
            experience_shift_career_pivot="NA",
            
            # Org
            org_map_boss_peers_reports="NA",
            
            # OKRs
            internal_okrs_scorecards="NA",
            
            # Events
            event_activity_speaker_exhibitor="NA",
            
            # Polls
            poll_participation_ai_cost_regulation="NA",
            
            # Breakage
            breakage_claims_rollout_governance="NA"
        )
    
    @staticmethod
    def _split_email_content(email_content: str) -> List[str]:
        """Split email content into sections for each prospect"""
        # Look for section separators like "EMAIL 1:", "PROSPECT:", etc.
        sections = re.split(r'(?:EMAIL \d+|PROSPECT \d+|---+)', email_content, flags=re.IGNORECASE)
        return [section.strip() for section in sections if section.strip()]
    
    @staticmethod
    def _parse_email_section(section: str, research):
        """Parse individual email section"""
        from email_automation import EmailOutput
        # Extract subject line
        subject_match = re.search(r'subject:?\s*(.+)', section, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else f"Your AI initiatives at {research.company_name}"
        
        # Extract message 1
        msg1_match = re.search(r'message\s*#?1:?\s*(.*?)(?=message\s*#?2|$)', section, re.IGNORECASE | re.DOTALL)
        msg1 = msg1_match.group(1).strip() if msg1_match else "Personalized message to be generated"
        
        # Extract message 2
        msg2_match = re.search(r'message\s*#?2:?\s*(.*)', section, re.IGNORECASE | re.DOTALL)
        msg2 = msg2_match.group(1).strip() if msg2_match else "Follow-up message to be generated"
        
        return EmailOutput(
            person_name=research.person_name,
            company_name=research.company_name,
            email_subject=subject,
            email_body_msg1=msg1,
            email_body_msg2=msg2
        )
    
    @staticmethod
    def _create_fallback_email(research):
        """Create fallback email when parsing fails"""
        from email_automation import EmailOutput
        return EmailOutput(
            person_name=research.person_name,
            company_name=research.company_name,
            email_subject=f"Your AI initiatives at {research.company_name}",
            email_body_msg1=f"Hi {research.person_name.split()[0]}, I noticed your work in AI/ML at {research.company_name}. TrueFoundry helps teams like yours move from prototype to production faster. Would love to share how companies like NVIDIA and Mastercard have achieved measurable AI ROI with our platform.",
            email_body_msg2=f"Following up on my previous message - I was reading about {research.company_name}'s AI initiatives and wanted to ask about your current infrastructure challenges. We've helped similar companies with MLOps, scaling, and cost optimization. Would you be open to a brief conversation?"
        )

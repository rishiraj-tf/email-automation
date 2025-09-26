"""
Parsing utilities for LLM responses
"""

import csv
import re
import json
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
            
            # Parse CSV with proper handling of multi-line fields
            csv_file = StringIO(cleaned_content)
            
            # Use proper CSV parsing settings for multi-line quoted fields
            reader = csv.DictReader(csv_file, quoting=csv.QUOTE_ALL, skipinitialspace=True)
            
            parsed_rows = []
            try:
                for row_num, row in enumerate(reader):
                    logger.info(f"Parsing CSV row {row_num + 1}: {row.get('person_name', 'Unknown')}")
                    parsed_rows.append(row)
            except Exception as csv_error:
                logger.error(f"CSV parsing failed at row {len(parsed_rows) + 1}: {csv_error}")
                # Log more details about the CSV structure
                csv_file.seek(0)
                all_content = csv_file.read()
                logger.error(f"Total CSV content length: {len(all_content)}")
                logger.error(f"CSV content sample: {all_content[:2000]}...")
                
                # Count lines to debug
                lines = all_content.split('\n')
                logger.error(f"CSV has {len(lines)} total lines")
                for i in range(min(5, len(lines))):
                    logger.error(f"Line {i+1}: {lines[i][:150]}...")
                
                # Try alternative parsing approach
                logger.info("Attempting alternative CSV parsing...")
                try:
                    csv_file.seek(0)
                    # Try with different quoting options
                    reader_alt = csv.DictReader(csv_file, quoting=csv.QUOTE_MINIMAL)
                    for row_num, row in enumerate(reader_alt):
                        logger.info(f"Alt parsing row {row_num + 1}: {row.get('person_name', 'Unknown')}")
                        parsed_rows.append(row)
                except Exception as alt_error:
                    logger.error(f"Alternative parsing also failed: {alt_error}")
                    raise csv_error
            
            logger.info(f"Successfully parsed {len(parsed_rows)} rows from CSV")
            
            # Match with original prospects and create ResearchOutput objects
            for i, prospect in enumerate(original_prospects):
                if i < len(parsed_rows):
                    row = parsed_rows[i]
                    result = LLMResponseParser._create_research_output(row, prospect)
                else:
                    # Fail fast - no fallback parsing
                    logger.error(f"No CSV row for prospect {i+1}: {prospect.person_name}")
                    logger.error(f"Total parsed rows: {len(parsed_rows)}, Expected: {len(original_prospects)}")
                    raise Exception(f"CSV parsing incomplete: Only {len(parsed_rows)} rows parsed, expected {len(original_prospects)}")
                
                results.append(result)
                
        except Exception as e:
            logger.error(f"Failed to parse research CSV: {e}")
            logger.error(f"CSV content preview: {csv_content[:1000]}")
            logger.error(f"Cleaned content preview: {cleaned_content[:1000] if 'cleaned_content' in locals() else 'Not available'}")
            if 'parsed_rows' in locals():
                logger.error(f"Parsed rows: {len(parsed_rows)}, Expected: {len(original_prospects)}")
            # Re-raise to see the actual error
            raise
        
        return results
    
    @staticmethod
    def parse_research_json(json_content: str, original_prospects: List):
        """
        Parse research JSON content from LLM response
        
        Args:
            json_content: Raw JSON content from LLM
            original_prospects: Original prospect data for validation
            
        Returns:
            List of ResearchOutput objects
        """
        from email_automation import ResearchOutput
        results = []
        
        logger.info(f"Starting to parse research JSON for {len(original_prospects)} prospects")
        logger.info(f"JSON content length: {len(json_content)}")
        logger.info(f"JSON content preview: {json_content[:300]}...")
        
        try:
            # Clean JSON content
            cleaned_json = LLMResponseParser._clean_json_content(json_content)
            logger.info(f"Cleaned JSON length: {len(cleaned_json)}")
            
            # Parse JSON directly - fail fast if invalid
            research_data = json.loads(cleaned_json)
            logger.info(f"Successfully parsed JSON with {len(research_data)} objects")
            
            # Validate it's an array
            if not isinstance(research_data, list):
                raise Exception("JSON response is not an array")
            
            # Process each research object
            for i, prospect in enumerate(original_prospects):
                if i < len(research_data):
                    research_obj = research_data[i]
                    logger.info(f"Processing research for prospect {i+1}: {prospect.person_name}")
                    result = LLMResponseParser._create_research_from_json(research_obj, prospect)
                else:
                    logger.error(f"No JSON object for prospect {i+1}: {prospect.person_name}")
                    raise Exception(f"JSON parsing incomplete: Only {len(research_data)} objects found, expected {len(original_prospects)}")
                
                results.append(result)
            
            logger.info(f"Successfully created {len(results)} research results from JSON")
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"JSON content that failed: {json_content[:1000]}")
            logger.error(f"Cleaned JSON that failed: {cleaned_json[:1000]}")
            raise Exception(f"Invalid JSON format from LLM: {e}")
            
        except Exception as e:
            logger.error(f"Failed to parse research JSON: {e}")
            logger.error(f"JSON content: {json_content[:1000]}")
            if 'research_data' in locals():
                logger.error(f"Parsed {len(research_data)} JSON objects, expected {len(original_prospects)}")
            raise
    
    @staticmethod
    def _clean_json_content(json_content: str) -> str:
        """Clean JSON content from LLM response"""
        logger.info(f"Starting JSON cleaning, original length: {len(json_content)}")
        
        # Remove markdown code blocks
        json_content = re.sub(r'```json\s*', '', json_content)
        json_content = re.sub(r'```\s*', '', json_content)
        
        # Remove any explanatory text before/after JSON
        json_content = json_content.strip()
        
        # Find the JSON array bounds
        start_idx = json_content.find('[')
        end_idx = json_content.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_content = json_content[start_idx:end_idx + 1]
        else:
            # No valid JSON array found
            logger.error("No valid JSON array found in response")
            raise Exception("No valid JSON array found in LLM response")
        
        logger.info(f"JSON cleaning completed, final length: {len(json_content)}")
        return json_content
    
    @staticmethod
    def _create_research_from_json(json_obj: Dict[str, Any], prospect):
        """Create ResearchOutput from simplified JSON object (LinkedIn DM essentials only)"""
        from email_automation import ResearchOutput
        
        # Helper function to get value with fallback
        def get_field(field_name: str, fallback: str = "NA") -> str:
            value = json_obj.get(field_name, fallback)
            return str(value) if value else fallback
        
        # Map simplified fields to full ResearchOutput structure
        return ResearchOutput(
            person_name=get_field('person_name', prospect.person_name),
            company_name=get_field('company_name', prospect.company_name),
            linkedin_url=prospect.linkedin_url,  # Use original
            
            # Map the essential fields from simplified JSON
            general_report=get_field('person_ai_project'),  # Person's AI project
            ai_ml_initiatives=get_field('company_ai_initiatives'),  # Company AI initiatives  
            key_challenges_solving=get_field('key_challenges'),  # Their challenges
            how_truefoundry_can_help=get_field('how_truefoundry_can_help'),  # Specific TrueFoundry value
            personal_details=get_field('person_name', prospect.person_name),
            
            # Set minimal defaults for all other fields (not needed for LinkedIn DM)
            executive_urgency_earnings_board_mentions="NA",
            executive_urgency_infra_costs="NA", 
            regulatory_compliance_deadlines="NA",
            regulatory_soc2_eu_ai_act="NA",
            incident_outage_rollback="NA",
            competitive_stack_usage_rival_vendors="NA",
            fresh_funding_partnerships="NA",
            hiring_spikes_ml_ops_ai_infra="NA",
            metric_targets_sla_arr_csat_cost="NA",
            negative_triggers_layoffs_churn_failed_pocs="NA",
            technical_deployment_on_prem_provider="NA",
            technical_deployment_cloud_providers="NA", 
            production_maturity_inference_volume="NA",
            production_maturity_fda_cleared="NA",
            conference_webinar_quotes="NA",
            recent_ai_posts_comments_90_days="NA",
            experience_shift_career_pivot="NA",
            org_map_boss_peers_reports="NA", 
            internal_okrs_scorecards="NA",
            event_activity_speaker_exhibitor="NA",
            poll_participation_ai_cost_regulation="NA",
            breakage_claims_rollout_governance="NA"
        )
    
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
                    # Fail fast - no fallback parsing
                    logger.error(f"No email section for prospect {i+1}: {research.person_name}")
                    logger.error(f"Total email sections: {len(email_sections)}, Expected: {len(research_results)}")
                    raise Exception(f"Email parsing incomplete: Only {len(email_sections)} sections found, expected {len(research_results)}")
                
                emails.append(email)
                
        except Exception as e:
            logger.error(f"Failed to parse email content: {e}")
            logger.error(f"Email content preview: {email_content[:1000]}")
            if 'email_sections' in locals():
                logger.error(f"Email sections found: {len(email_sections)}, Expected: {len(research_results)}")
            # Re-raise to see the actual error
            raise
        
        return emails
    
    @staticmethod
    def _clean_csv_content(csv_content: str) -> str:
        """Clean CSV content from LLM response"""
        # Remove markdown code blocks
        csv_content = re.sub(r'```csv\s*', '', csv_content)
        csv_content = re.sub(r'```\s*', '', csv_content)
        
        # Don't split by lines for multi-line CSV fields
        # Just clean up the content and return it
        csv_content = csv_content.strip()
        
        logger.info(f"CSV cleaning - Original length: {len(csv_content)}")
        logger.info(f"CSV cleaning - First 500 chars: {csv_content[:500]}")
        
        return csv_content
    
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
    def _split_email_content(email_content: str) -> List[str]:
        """Split email content into sections for each prospect"""
        # Look for section separators like "PROSPECT 1:", "PROSPECT 2:", etc.
        logger.info(f"Splitting email content of length: {len(email_content)}")
        
        # Split by PROSPECT N: pattern
        sections = re.split(r'(?:PROSPECT\s*\d+:|EMAIL\s*\d+:|={3,})', email_content, flags=re.IGNORECASE)
        
        # Filter out empty sections
        sections = [section.strip() for section in sections if section.strip()]
        
        logger.info(f"Found {len(sections)} email sections")
        for i, section in enumerate(sections[:2]):  # Log first 2 sections
            logger.info(f"Section {i+1} preview: {section[:100]}...")
            
        return sections
    
    @staticmethod
    def _parse_email_section(section: str, research):
        """Parse individual email section"""
        from email_automation import EmailOutput
        # Extract subject line
        subject_match = re.search(r'subject:?\s*(.+)', section, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else f"Your AI initiatives at {research.company_name}"
        
        # Extract message 1 - try multiple patterns
        msg1 = "Personalized message to be generated"
        
        # Pattern 1: MESSAGE #1:
        msg1_match = re.search(r'message\s*#?1:?\s*(.*?)(?=message\s*#?2|$)', section, re.IGNORECASE | re.DOTALL)
        if msg1_match:
            msg1 = msg1_match.group(1).strip()
        else:
            # Pattern 2: Part 2: LinkedIn DM
            linkedin_dm_match = re.search(r'part\s*2:?\s*linkedin\s*dm\s*(.*?)(?=part\s*3|$)', section, re.IGNORECASE | re.DOTALL)
            if linkedin_dm_match:
                msg1 = linkedin_dm_match.group(1).strip()
            else:
                # Pattern 3: Try to extract LinkedIn DM that starts with "Hi"
                hi_match = re.search(r'(Hi\s+\w+,.*?)(?=\n\s*$|\Z)', section, re.IGNORECASE | re.DOTALL)
                if hi_match:
                    msg1 = hi_match.group(1).strip()
        
        # Clean up the message
        if msg1:
            msg1 = msg1.strip()
        
        return EmailOutput(
            person_name=research.person_name,
            company_name=research.company_name,
            email_subject=subject,
            email_body_msg1=msg1,
            email_body_msg2=""  # Only MESSAGE #1 as requested
        )
    

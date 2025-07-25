#!/usr/bin/env python3
"""
Dataverse BotComponents Analysis Script

This script analyzes the botcomponents table in Dataverse to understand:
1. All component types and their counts
2. Components related to knowledge/file storage
3. Components with actual content data
4. Components related to "Nate's Hardware Buddy" or similar names

Usage:
    python3 analyze_botcomponents.py
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from dotenv import load_dotenv
import requests
from msal import ConfidentialClientApplication

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataverseAnalyzer:
    def __init__(self):
        """Initialize the Dataverse analyzer with authentication."""
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.dataverse_url = os.getenv('DATAVERSE_URL')
        self.copilot_agent_name = os.getenv('COPILOT_AGENT_NAME', "Nate's Hardware Buddy")
        
        if not all([self.tenant_id, self.client_id, self.client_secret, self.dataverse_url]):
            raise ValueError("Missing required environment variables for Dataverse authentication")
        
        self.access_token = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Azure AD to get access token for Dataverse."""
        try:
            app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Get token for Dataverse
            scope = [f"{self.dataverse_url}/.default"]
            result = app.acquire_token_for_client(scopes=scope)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                logger.info("Successfully authenticated with Dataverse")
            else:
                raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def _make_dataverse_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Dataverse API."""
        if not self.access_token:
            raise Exception("No access token available")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0'
        }
        
        url = f"{self.dataverse_url}/api/data/v9.2/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Dataverse API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def analyze_component_types(self) -> Dict[str, Any]:
        """Analyze all component types in the botcomponents table."""
        logger.info("Analyzing component types...")
        
        # Get all botcomponents with component type counts
        params = {
            '$select': 'componenttype,name,content,statecode,statuscode,createdon,modifiedon',
            '$orderby': 'componenttype,createdon desc'
        }
        
        all_components = []
        next_link = None
        
        # Handle pagination
        while True:
            if next_link:
                response = requests.get(
                    next_link,
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Accept': 'application/json',
                        'OData-MaxVersion': '4.0',
                        'OData-Version': '4.0'
                    }
                )
                response.raise_for_status()
                data = response.json()
            else:
                data = self._make_dataverse_request('botcomponents', params)
            
            all_components.extend(data.get('value', []))
            
            next_link = data.get('@odata.nextLink')
            if not next_link:
                break
            
            logger.info(f"Retrieved {len(all_components)} components so far...")
        
        logger.info(f"Total components retrieved: {len(all_components)}")
        
        # Analyze component types
        type_counts = Counter()
        type_examples = defaultdict(list)
        content_analysis = defaultdict(int)
        hardware_related = []
        
        for component in all_components:
            comp_type = component.get('componenttype', 'Unknown')
            name = component.get('name', 'Unnamed')
            content = component.get('content', '')
            
            type_counts[comp_type] += 1
            
            # Keep examples of each type (limit to 3)
            if len(type_examples[comp_type]) < 3:
                type_examples[comp_type].append({
                    'name': name,
                    'has_content': bool(content and content.strip()),
                    'content_length': len(content) if content else 0,
                    'statecode': component.get('statecode'),
                    'createdon': component.get('createdon'),
                    'modifiedon': component.get('modifiedon')
                })
            
            # Count components with actual content
            if content and content.strip():
                content_analysis[comp_type] += 1
            
            # Look for hardware/knowledge related components
            search_terms = ['hardware', 'nate', 'buddy', 'knowledge', 'file', 'document', 'upload']
            if any(term.lower() in name.lower() for term in search_terms):
                hardware_related.append({
                    'componenttype': comp_type,
                    'name': name,
                    'has_content': bool(content and content.strip()),
                    'content_preview': content[:200] if content else '',
                    'statecode': component.get('statecode'),
                    'createdon': component.get('createdon')
                })
        
        return {
            'total_components': len(all_components),
            'component_type_counts': dict(type_counts),
            'component_type_examples': dict(type_examples),
            'components_with_content_by_type': dict(content_analysis),
            'hardware_related_components': hardware_related,
            'component_types_summary': self._get_component_types_summary(type_counts, content_analysis)
        }

    def _get_component_types_summary(self, type_counts: Counter, content_analysis: Dict) -> Dict[str, Dict]:
        """Create a summary of component types with their likely purposes."""
        
        # Known component type mappings (based on common Copilot Studio patterns)
        known_types = {
            2: "Topics/Dialogs",
            7: "Entities", 
            9: "Variables/Settings",
            10: "Knowledge Sources/Files",
            15: "Triggers/Events",
            16: "Actions/Skills"
        }
        
        summary = {}
        for comp_type, count in type_counts.most_common():
            content_count = content_analysis.get(comp_type, 0)
            summary[str(comp_type)] = {
                'total_count': count,
                'components_with_content': content_count,
                'content_percentage': round((content_count / count * 100), 1) if count > 0 else 0,
                'likely_purpose': known_types.get(comp_type, "Unknown"),
                'is_knowledge_candidate': comp_type == 10 or (content_count / count > 0.8 if count > 0 else False)
            }
        
        return summary

    def analyze_knowledge_components(self) -> Dict[str, Any]:
        """Deep dive into components that likely contain knowledge/file data."""
        logger.info("Analyzing potential knowledge components...")
        
        # Focus on components with substantial content
        params = {
            '$select': 'componenttype,name,content,statecode,statuscode,createdon,modifiedon',
            '$filter': 'content ne null and content ne \'\'',
            '$orderby': 'componenttype,modifiedon desc'
        }
        
        data = self._make_dataverse_request('botcomponents', params)
        components_with_content = data.get('value', [])
        
        knowledge_analysis = defaultdict(list)
        
        for component in components_with_content:
            comp_type = component.get('componenttype')
            name = component.get('name', 'Unnamed')
            content = component.get('content', '')
            
            # Analyze content to determine if it's knowledge-related
            content_indicators = {
                'is_json': content.strip().startswith('{') or content.strip().startswith('['),
                'contains_file_references': any(ext in content.lower() for ext in ['.txt', '.pdf', '.doc', '.md']),
                'contains_knowledge_keywords': any(kw in content.lower() for kw in ['knowledge', 'file', 'document', 'upload', 'source']),
                'is_large_content': len(content) > 1000,
                'contains_td_synnex': 'td synnex' in content.lower() or 'synnex' in content.lower()
            }
            
            knowledge_analysis[comp_type].append({
                'name': name,
                'content_length': len(content),
                'content_preview': content[:500],
                'content_indicators': content_indicators,
                'statecode': component.get('statecode'),
                'createdon': component.get('createdon'),
                'modifiedon': component.get('modifiedon')
            })
        
        return {
            'total_components_with_content': len(components_with_content),
            'knowledge_components_by_type': dict(knowledge_analysis),
            'recommended_knowledge_types': self._identify_knowledge_types(knowledge_analysis)
        }

    def _identify_knowledge_types(self, knowledge_analysis: Dict) -> List[Dict]:
        """Identify which component types are most likely used for knowledge storage."""
        recommendations = []
        
        for comp_type, components in knowledge_analysis.items():
            if not components:
                continue
            
            # Calculate knowledge indicators
            total_components = len(components)
            large_content_count = sum(1 for c in components if c['content_indicators']['is_large_content'])
            file_ref_count = sum(1 for c in components if c['content_indicators']['contains_file_references'])
            knowledge_kw_count = sum(1 for c in components if c['content_indicators']['contains_knowledge_keywords'])
            
            knowledge_score = (
                (large_content_count / total_components * 40) +
                (file_ref_count / total_components * 30) +
                (knowledge_kw_count / total_components * 30)
            )
            
            if knowledge_score > 20:  # Threshold for knowledge components
                recommendations.append({
                    'component_type': comp_type,
                    'total_components': total_components,
                    'knowledge_score': round(knowledge_score, 1),
                    'characteristics': {
                        'large_content_percentage': round(large_content_count / total_components * 100, 1),
                        'file_references_percentage': round(file_ref_count / total_components * 100, 1),
                        'knowledge_keywords_percentage': round(knowledge_kw_count / total_components * 100, 1)
                    }
                })
        
        return sorted(recommendations, key=lambda x: x['knowledge_score'], reverse=True)

    def search_copilot_agent(self) -> Dict[str, Any]:
        """Search for components related to the specific Copilot agent."""
        logger.info(f"Searching for components related to '{self.copilot_agent_name}'...")
        
        # Search variations of the agent name
        search_terms = [
            self.copilot_agent_name,
            "Nate's Hardware Buddy",
            "Hardware Buddy",
            "Nate Hardware",
            "hardware",
            "buddy"
        ]
        
        related_components = []
        
        for term in search_terms:
            params = {
                '$select': 'componenttype,name,content,statecode,statuscode,createdon,modifiedon',
                '$filter': f"contains(tolower(name), '{term.lower()}')"
            }
            
            try:
                data = self._make_dataverse_request('botcomponents', params)
                components = data.get('value', [])
                
                for component in components:
                    if component not in related_components:  # Avoid duplicates
                        component['search_term_matched'] = term
                        related_components.append(component)
                        
            except Exception as e:
                logger.warning(f"Search for '{term}' failed: {e}")
                continue
        
        return {
            'agent_name': self.copilot_agent_name,
            'related_components': related_components,
            'component_types_found': list(set(c.get('componenttype') for c in related_components))
        }

    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        logger.info("Generating comprehensive analysis report...")
        
        # Run all analyses
        component_analysis = self.analyze_component_types()
        knowledge_analysis = self.analyze_knowledge_components()
        agent_analysis = self.search_copilot_agent()
        
        # Generate report
        report_lines = [
            "=" * 80,
            "DATAVERSE BOTCOMPONENTS ANALYSIS REPORT",
            "=" * 80,
            "",
            f"Analysis Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Dataverse URL: {self.dataverse_url}",
            f"Target Agent: {self.copilot_agent_name}",
            "",
            "1. COMPONENT TYPE SUMMARY",
            "-" * 40,
            f"Total Components: {component_analysis['total_components']:,}",
            ""
        ]
        
        # Component types breakdown
        for comp_type, details in component_analysis['component_types_summary'].items():
            report_lines.extend([
                f"Component Type {comp_type} ({details['likely_purpose']}):",
                f"  Total: {details['total_count']:,}",
                f"  With Content: {details['components_with_content']:,} ({details['content_percentage']}%)",
                f"  Knowledge Candidate: {'Yes' if details['is_knowledge_candidate'] else 'No'}",
                ""
            ])
        
        # Knowledge analysis
        report_lines.extend([
            "2. KNOWLEDGE COMPONENT ANALYSIS",
            "-" * 40,
            f"Components with Content: {knowledge_analysis['total_components_with_content']:,}",
            ""
        ])
        
        if knowledge_analysis['recommended_knowledge_types']:
            report_lines.append("Recommended Knowledge Storage Types:")
            for rec in knowledge_analysis['recommended_knowledge_types']:
                report_lines.extend([
                    f"  Type {rec['component_type']}: Score {rec['knowledge_score']}/100",
                    f"    Large Content: {rec['characteristics']['large_content_percentage']}%",
                    f"    File References: {rec['characteristics']['file_references_percentage']}%",
                    f"    Knowledge Keywords: {rec['characteristics']['knowledge_keywords_percentage']}%",
                    ""
                ])
        
        # Agent-specific analysis
        report_lines.extend([
            "3. COPILOT AGENT COMPONENTS",
            "-" * 40
        ])
        
        if agent_analysis['related_components']:
            report_lines.append(f"Found {len(agent_analysis['related_components'])} related components:")
            for component in agent_analysis['related_components'][:10]:  # Limit to first 10
                report_lines.append(f"  Type {component.get('componenttype')}: {component.get('name')}")
        else:
            report_lines.append("No components found related to the target agent.")
        
        # Recommendations
        report_lines.extend([
            "",
            "4. RECOMMENDATIONS FOR TD SYNNEX FILE UPLOAD",
            "-" * 50
        ])
        
        if knowledge_analysis['recommended_knowledge_types']:
            best_type = knowledge_analysis['recommended_knowledge_types'][0]
            report_lines.extend([
                f"Recommended Component Type: {best_type['component_type']}",
                f"Confidence Score: {best_type['knowledge_score']}/100",
                "",
                "Next Steps:",
                "1. Use component type {best_type['component_type']} for TD SYNNEX file uploads",
                "2. Monitor existing knowledge components for content structure patterns",
                "3. Test with small files before bulk upload"
            ])
        else:
            report_lines.extend([
                "Could not identify clear knowledge storage pattern.",
                "Recommend manual inspection of component types 10, 16, and 15."
            ])
        
        return "\n".join(report_lines)

def main():
    """Main execution function."""
    try:
        analyzer = DataverseAnalyzer()
        report = analyzer.generate_report()
        
        # Save report to file
        report_file = f"botcomponents_analysis_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"\nReport saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
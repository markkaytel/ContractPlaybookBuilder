"""
AI-powered playbook generation using Claude API.

This module generates comprehensive contract playbooks with detailed analysis
matching professional legal playbook standards, organized by contract topic.
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from anthropic import Anthropic
import config


def get_anthropic_client():
    """Get Anthropic client with API key from config."""
    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError(
            "Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable."
        )
    return Anthropic(api_key=api_key)


# Contract topic categories for organizing the playbook
CONTRACT_TOPICS = [
    "Definitions",
    "Solution/Services",
    "Licenses & Restrictions",
    "Proprietary Rights/IP",
    "Financial Terms",
    "Confidentiality",
    "Data Security & Privacy",
    "Warranties",
    "Indemnification",
    "Limitation of Liability",
    "Term & Termination",
    "General Provisions",
    "Exhibits & Schedules"
]


SYSTEM_PROMPT = """You are an expert contract attorney with 25+ years of experience creating comprehensive contract playbooks for Fortune 500 companies. You analyze contracts with extraordinary depth and practical insight.

Your analysis must be:
1. THOROUGH - Every significant clause gets detailed treatment
2. PRACTICAL - Real negotiation guidance, not academic analysis
3. BALANCED - Both customer and provider perspectives
4. ACTIONABLE - Ready-to-use fallback language and hard limits

For each clause you analyze, provide:
- The exact contract language (quoted)
- Why this clause exists and matters (business context)
- What customers typically want to change
- What providers need to protect
- Specific acceptable modifications
- Ready-to-use fallback language
- Clear "do not accept" boundaries"""


def analyze_contract_with_claude(
    contract_text: str,
    agreement_type: str = "General Agreement",
    user_role: str = "Customer",
    risk_tolerance: str = "Moderate",
    progress_callback=None
) -> dict:
    """
    Analyze contract using Claude API with topic-based organization.

    Returns a structured playbook matching the format of professional legal playbooks.
    """
    client = get_anthropic_client()

    if progress_callback:
        progress_callback(5, "Preparing contract analysis...")

    # First, get the overview and identify key sections
    overview_prompt = f"""Analyze this contract and provide a comprehensive overview.

CONTRACT TEXT:
{contract_text[:50000]}

CONTEXT:
- Agreement Type: {agreement_type}
- Analyzing from: {user_role} perspective
- Risk Tolerance: {risk_tolerance}

Provide your analysis as JSON with this structure:
{{
    "title": "Full title of the agreement",
    "parties": "Description of the parties",
    "effective_date": "If specified",
    "governing_law": "Jurisdiction if specified",
    "key_principles": [
        "Key principle 1 about this agreement",
        "Key principle 2",
        "Key principle 3",
        "Key principle 4"
    ],
    "executive_summary": "2-3 paragraph overview of the agreement and key negotiation considerations",
    "sections_found": ["List of major sections/topics found in the contract"]
}}"""

    if progress_callback:
        progress_callback(10, "Analyzing agreement structure...")

    overview_response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        messages=[
            {"role": "user", "content": overview_prompt}
        ],
        system=SYSTEM_PROMPT
    )

    try:
        overview_text = overview_response.content[0].text
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', overview_text)
        if json_match:
            overview = json.loads(json_match.group())
        else:
            overview = {"title": agreement_type, "key_principles": [], "executive_summary": ""}
    except (json.JSONDecodeError, IndexError):
        overview = {"title": agreement_type, "key_principles": [], "executive_summary": ""}

    # Analyze each topic area
    all_topics = {}
    quick_reference = []

    topics_to_analyze = [
        ("Definitions", "definitions, defined terms, and interpretation provisions"),
        ("Solution/Services", "the solution, services, platform, software, or product being provided"),
        ("Licenses & Restrictions", "license grants, usage rights, restrictions, and permitted uses"),
        ("Proprietary Rights/IP", "intellectual property, ownership, proprietary rights, and IP assignments"),
        ("Financial Terms", "fees, payment terms, pricing, invoicing, and financial obligations"),
        ("Confidentiality", "confidentiality, non-disclosure, and information protection"),
        ("Data Security & Privacy", "data protection, security, privacy, data processing, and compliance"),
        ("Warranties", "representations, warranties, disclaimers, and guarantees"),
        ("Indemnification", "indemnification, defense, and hold harmless provisions"),
        ("Limitation of Liability", "liability caps, exclusions, consequential damages, and limitations"),
        ("Term & Termination", "term, renewal, termination rights, and effects of termination"),
        ("General Provisions", "miscellaneous provisions like assignment, notices, force majeure, amendments"),
        ("Exhibits & Schedules", "exhibits, schedules, appendices, and attachments")
    ]

    def _analyze_single_topic(topic_name, topic_description):
        """Analyze a single contract topic. Designed to run in a thread."""
        topic_prompt = f"""Analyze this contract focusing specifically on {topic_description}.

CONTRACT TEXT:
{contract_text[:80000]}

CONTEXT:
- Agreement Type: {agreement_type}
- Analyzing from: {user_role} perspective
- Risk Tolerance: {risk_tolerance}

For each relevant clause or provision related to {topic_name}, provide detailed analysis.

Return JSON with this structure:
{{
    "topic": "{topic_name}",
    "clauses": [
        {{
            "section": "Section number (e.g., '2.1', 'III', 'Schedule A')",
            "subsection": "Subsection if applicable",
            "issue": "Brief title describing the specific issue",
            "current_language": "EXACT quoted text from the contract",
            "purpose_rationale": "Why this clause exists and its business purpose",
            "customer_concerns": "• Bullet point 1\\n• Bullet point 2\\n• Bullet point 3",
            "customer_edits_to_watch": "• Edit 1\\n• Edit 2\\n• Edit 3",
            "provider_position": "The provider's perspective and what they need to protect",
            "acceptable_modifications": "• Modification 1\\n• Modification 2",
            "fallback_language": "Ready-to-use alternative contract language",
            "do_not_accept": "• Hard limit 1\\n• Hard limit 2",
            "notes": "Additional considerations or context"
        }}
    ],
    "hard_limits": [
        {{
            "issue": "Brief description",
            "limit": "What requires executive approval"
        }}
    ]
}}

Be thorough - analyze EVERY clause related to {topic_name}. Include both explicit provisions AND important omissions that should be addressed."""

        topic_response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=8192,
            messages=[
                {"role": "user", "content": topic_prompt}
            ],
            system=SYSTEM_PROMPT
        )

        topic_text = topic_response.content[0].text
        json_match = re.search(r'\{[\s\S]*\}', topic_text)
        if json_match:
            topic_data = json.loads(json_match.group())
            return topic_name, topic_data.get("clauses", []), topic_data.get("hard_limits", [])
        return topic_name, [], []

    # Run topic analyses in parallel (5 workers balances speed vs rate limits)
    completed_count = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for topic_name, topic_description in topics_to_analyze:
            future = executor.submit(_analyze_single_topic, topic_name, topic_description)
            futures[future] = topic_name

        for future in as_completed(futures):
            topic_name = futures[future]
            completed_count += 1
            if progress_callback:
                progress = 15 + int((completed_count / len(topics_to_analyze)) * 70)
                progress_callback(progress, f"Analyzed {topic_name} ({completed_count}/{len(topics_to_analyze)})")
            try:
                name, clauses, hard_limits = future.result()
                if clauses:
                    all_topics[name] = clauses
                if hard_limits:
                    quick_reference.extend(hard_limits)
            except Exception as e:
                print(f"Error analyzing {topic_name}: {e}")

    if progress_callback:
        progress_callback(90, "Compiling playbook...")

    # Build the final playbook structure
    playbook = {
        "overview": {
            "title": overview.get("title", agreement_type),
            "agreement_type": agreement_type,
            "perspective": user_role,
            "parties": overview.get("parties", ""),
            "effective_date": overview.get("effective_date", ""),
            "governing_law": overview.get("governing_law", ""),
            "key_principles": overview.get("key_principles", []),
            "executive_summary": overview.get("executive_summary", ""),
            "how_to_use": [
                "Navigate to the relevant section tab based on the clause being negotiated",
                "Review the 'Purpose/Rationale' to understand why the clause exists",
                "Check 'Customer Concerns' or 'Provider Position' based on your role",
                "Use 'Acceptable Modifications' for standard negotiation moves",
                "Reference 'Fallback Language' when proposing alternatives",
                "Never accept terms listed in 'Do Not Accept' without executive approval"
            ]
        },
        "topics": all_topics,
        "quick_reference": quick_reference
    }

    if progress_callback:
        progress_callback(100, "Analysis complete")

    return playbook


def analyze_contract_chunked(
    contract_text: str,
    agreement_type: str = "General Agreement",
    user_role: str = "Customer",
    risk_tolerance: str = "Moderate",
    progress_callback=None
) -> dict:
    """
    Main entry point - routes to Claude API.
    Maintains backward compatibility with existing code.
    """
    return analyze_contract_with_claude(
        contract_text=contract_text,
        agreement_type=agreement_type,
        user_role=user_role,
        risk_tolerance=risk_tolerance,
        progress_callback=progress_callback
    )

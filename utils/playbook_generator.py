"""
AI-powered playbook generation using Claude API or OpenAI-compatible APIs.

This module generates comprehensive contract playbooks with detailed analysis
matching professional legal playbook standards, organized by contract topic.
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from anthropic import Anthropic
from openai import OpenAI
import config


def get_ai_client():
    """Get AI client based on configuration (Anthropic or OpenAI-compatible)."""
    if config.AI_PROVIDER == "anthropic":
        api_key = config.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable."
            )
        return ("anthropic", Anthropic(api_key=api_key))
    else:
        # OpenAI or OpenAI-compatible API
        api_key = config.OPENAI_API_KEY
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
            )

        # Create OpenAI client with optional custom base URL
        client_kwargs = {"api_key": api_key}
        if config.OPENAI_BASE_URL:
            client_kwargs["base_url"] = config.OPENAI_BASE_URL

        return ("openai", OpenAI(**client_kwargs))


def get_anthropic_client():
    """Legacy function for backward compatibility."""
    provider, client = get_ai_client()
    if provider != "anthropic":
        raise ValueError("Anthropic provider not configured")
    return client


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

# Detailed topic descriptions used for AI analysis prompts
CONTRACT_TOPICS_WITH_DESCRIPTIONS = [
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

    topics_to_analyze = list(CONTRACT_TOPICS_WITH_DESCRIPTIONS)

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


def call_ai_api(client, provider, prompt, system_prompt, max_tokens=4096):
    """
    Unified function to call either Anthropic or OpenAI-compatible APIs.

    Args:
        client: The AI client (Anthropic or OpenAI)
        provider: "anthropic" or "openai"
        prompt: The user prompt
        system_prompt: The system prompt
        max_tokens: Maximum tokens to generate

    Returns:
        The response text from the AI
    """
    if provider == "anthropic":
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            system=system_prompt
        )
        return response.content[0].text
    else:
        # OpenAI or OpenAI-compatible API
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content


def _build_guidance_context(guidance_documents: str) -> str:
    """Build guidance context string from guidance documents text."""
    if not guidance_documents:
        return ""
    return f"""

GUIDANCE DOCUMENTS PROVIDED:
The following internal guidance documents, policies, and playbook resources have been provided to inform this analysis.
Use these to align the playbook with organizational standards, preferred positions, and negotiation strategies:

{guidance_documents[:100000]}

When analyzing the contract, incorporate insights from these guidance documents, including:
- Organizational negotiation positions and preferences
- Standard fallback language and acceptable modifications
- Risk tolerance thresholds and escalation criteria
- Preferred contract terms and must-have provisions
- Hard limits and non-negotiable positions
"""


def analyze_contract_overview(
    contract_text: str,
    agreement_type: str = "General Agreement",
    user_role: str = "Customer",
    risk_tolerance: str = "Moderate",
    web_resources: str = "",
    guidance_documents: str = ""
) -> dict:
    """
    Phase 1: Analyze contract overview and suggest relevant topics.

    Returns overview data including title, summary, and suggested topics
    with relevance indicators for user selection.
    """
    provider, client = get_ai_client()
    guidance_context = _build_guidance_context(guidance_documents)

    # Build the standard topics list for the prompt
    standard_topics_list = "\n".join(
        f"- {name}: {desc}" for name, desc in CONTRACT_TOPICS_WITH_DESCRIPTIONS
    )

    overview_prompt = f"""Analyze this contract and provide a comprehensive overview AND topic relevance assessment.

CONTRACT TEXT:
{contract_text[:50000]}

{web_resources}

{guidance_context}

CONTEXT:
- Agreement Type: {agreement_type}
- Analyzing from: {user_role} perspective
- Risk Tolerance: {risk_tolerance}

STANDARD TOPICS TO ASSESS:
{standard_topics_list}

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
    "sections_found": ["List of major sections/topics found in the contract"],
    "suggested_topics": [
        {{
            "name": "Topic Name",
            "description": "Brief description of what this topic covers in this contract",
            "relevance": "high or medium or low",
            "found_in_contract": true,
            "is_standard": true
        }}
    ],
    "additional_topics": [
        {{
            "name": "Custom Topic Name specific to this contract",
            "description": "Why this additional topic is relevant to this specific agreement",
            "relevance": "high or medium",
            "found_in_contract": true,
            "is_standard": false
        }}
    ]
}}

For suggested_topics: evaluate EACH of the 13 standard topics listed above. Set found_in_contract to true if the contract contains relevant provisions, and relevance to "high", "medium", or "low" based on importance.

For additional_topics: suggest up to 5 additional topics that are specific to THIS contract and not covered by the standard topics (e.g., "Insurance Requirements", "Service Level Agreements", "Change Management", "Audit Rights", etc.). Only suggest topics that are actually present or notably absent from the contract."""

    try:
        overview_text = call_ai_api(client, provider, overview_prompt, SYSTEM_PROMPT, max_tokens=4096)
        json_match = re.search(r'\{[\s\S]*\}', overview_text)
        if json_match:
            overview = json.loads(json_match.group())
        else:
            overview = {"title": agreement_type, "key_principles": [], "executive_summary": "", "suggested_topics": [], "additional_topics": []}
    except (json.JSONDecodeError, IndexError, Exception) as e:
        print(f"Error parsing overview: {e}")
        # Fallback: return all standard topics as suggestions
        overview = {
            "title": agreement_type,
            "key_principles": [],
            "executive_summary": "",
            "suggested_topics": [
                {"name": name, "description": desc, "relevance": "medium", "found_in_contract": True, "is_standard": True}
                for name, desc in CONTRACT_TOPICS_WITH_DESCRIPTIONS
            ],
            "additional_topics": []
        }

    return overview


def analyze_contract_with_ai(
    contract_text: str,
    agreement_type: str = "General Agreement",
    user_role: str = "Customer",
    risk_tolerance: str = "Moderate",
    progress_callback=None,
    web_resources: str = "",
    guidance_documents: str = "",
    selected_topics: list = None,
    overview_data: dict = None
) -> dict:
    """
    Analyze contract using configured AI provider (Anthropic or OpenAI-compatible).

    Returns a structured playbook matching the format of professional legal playbooks.

    Args:
        selected_topics: Optional list of {"name": ..., "description": ...} dicts.
                        If provided, only these topics are analyzed instead of the default 13.
        overview_data: Optional cached overview from Phase 1 (analyze_contract_overview).
                      If provided, skips the overview AI call.
    """
    provider, client = get_ai_client()

    if progress_callback:
        progress_callback(5, "Preparing contract analysis...")

    # Build guidance context if provided
    guidance_context = _build_guidance_context(guidance_documents)

    # Reuse cached overview or fetch fresh
    if overview_data:
        overview = overview_data
    else:
        # First, get the overview and identify key sections
        overview_prompt = f"""Analyze this contract and provide a comprehensive overview.

CONTRACT TEXT:
{contract_text[:50000]}

{web_resources}

{guidance_context}

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

        try:
            overview_text = call_ai_api(client, provider, overview_prompt, SYSTEM_PROMPT, max_tokens=4096)
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', overview_text)
            if json_match:
                overview = json.loads(json_match.group())
            else:
                overview = {"title": agreement_type, "key_principles": [], "executive_summary": ""}
        except (json.JSONDecodeError, IndexError, Exception) as e:
            print(f"Error parsing overview: {e}")
            overview = {"title": agreement_type, "key_principles": [], "executive_summary": ""}

    # Analyze each topic area
    all_topics = {}
    quick_reference = []

    # Use selected topics if provided, otherwise use default list
    if selected_topics:
        topics_to_analyze = [
            (t["name"], t.get("description", t["name"])) for t in selected_topics
        ]
    else:
        topics_to_analyze = list(CONTRACT_TOPICS_WITH_DESCRIPTIONS)

    for idx, (topic_name, topic_description) in enumerate(topics_to_analyze):
        if progress_callback:
            progress = 15 + int((idx / len(topics_to_analyze)) * 70)
            progress_callback(progress, f"Analyzing {topic_name}...")

        topic_prompt = f"""Analyze this contract focusing specifically on {topic_description}.

CONTRACT TEXT:
{contract_text[:80000]}

{web_resources}

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

        try:
            topic_text = call_ai_api(client, provider, topic_prompt, SYSTEM_PROMPT, max_tokens=8192)
            json_match = re.search(r'\{[\s\S]*\}', topic_text)
            if json_match:
                topic_data = json.loads(json_match.group())
                if topic_data.get("clauses"):
                    all_topics[topic_name] = topic_data["clauses"]
                if topic_data.get("hard_limits"):
                    quick_reference.extend(topic_data["hard_limits"])
        except Exception as e:
            print(f"Error analyzing {topic_name}: {e}")
            continue

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
    progress_callback=None,
    web_resources: str = "",
    guidance_documents: str = "",
    selected_topics: list = None,
    overview_data: dict = None
) -> dict:
    """
    Main entry point - routes to configured AI provider.
    Supports both Anthropic Claude and OpenAI-compatible APIs.

    Args:
        selected_topics: Optional list of {"name": ..., "description": ...} dicts.
        overview_data: Optional cached overview from Phase 1.
    """
    return analyze_contract_with_ai(
        contract_text=contract_text,
        agreement_type=agreement_type,
        user_role=user_role,
        risk_tolerance=risk_tolerance,
        progress_callback=progress_callback,
        web_resources=web_resources,
        guidance_documents=guidance_documents,
        selected_topics=selected_topics,
        overview_data=overview_data
    )

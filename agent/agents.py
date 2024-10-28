from groq_model import GroqJsonModel,GroqModel
from state import AgentGraph
from utils import get_current_time_and_date
from prompts import planner_prompt_template, selector_prompt_template,reporter_prompt_template
from typing import Any, List
from tools import serpapi_search
import json
from termcolor import colored
from typing import Dict, Any
from tools import scrape_url


def parse_agent_response(agent_name: str, output: Any) -> dict:
    """Parse the response content based on agent type"""
    try:
        # First try to parse the content if it's a string or has content attribute
        if isinstance(output, str):
            try:
                content = json.loads(output)
            except json.JSONDecodeError:
                content = output
        elif hasattr(output, 'content'):
            try:
                content = json.loads(output.content)
            except json.JSONDecodeError:
                content = output.content
        else:
            content = output
            
        if agent_name == "PLANNER":
            return {
                "search_term": content.get("search_term", "N/A"),
                "overall_strategy": content.get("overall_strategy", "N/A"),
                "additional_information": content.get("additional_information", "N/A")
            }
        elif agent_name == "SELECTOR":
            return {
                "selected_page_url": content.get("selected_page_url", "N/A"),
                "description": content.get("description", "N/A"),
                "reason_for_selection": content.get("reason_for_selection", "N/A")
            }
        elif agent_name == "SCRAPER":
            # Handle dictionary with URL, title, and content
            if isinstance(content, dict):
                if "error" in content:
                    return content
                
                url = content.get("url", content.get("URL", "N/A"))
                title = content.get("title", content.get("Title", "N/A"))
                raw_content = content.get("content", content.get("Content", ""))
                
                # Only return if we have actual content
                if url != "N/A" or title != "N/A" or raw_content:
                    return {
                        "url": url,
                        "title": title,
                        "content_preview": f"{raw_content[:200]}..." if raw_content else "N/A"
                    }
            
            # If we get here, treat the content as raw text
            if content and str(content).strip():
                return {"raw_content": str(content)}
            
            return {"error": "No valid content found"}
        elif agent_name == "REPORTER":
            # For reporter, just return the raw content without parsing
            if hasattr(content, 'content'):
                return {"report": content.content}
            return {"report": str(content)}
        else:
            return content
    except Exception as e:
        return {"error": f"Error parsing content: {str(e)}", "raw_content": str(output)}

def format_parsed_content(content: dict) -> str:
    """Format the parsed content for display"""
    output_lines = []
    
    # Handle error messages first
    if "error" in content:
        return colored(f"ERROR: {content['error']}", "red")
    
    # Handle reporter content
    if "report" in content:
        return str(content["report"])
    
    # Handle raw content
    if "raw_content" in content:
        output_lines.append("Raw Content:")
        output_lines.append("-" * 40)
        output_lines.append(str(content["raw_content"]))
        output_lines.append("-" * 40)
        return "\n".join(output_lines)
    
    # Handle structured content
    for key, value in content.items():
        if value and value != "N/A":  # Only show non-empty and non-N/A values
            key_formatted = key.replace('_', ' ').title()
            output_lines.append(f"{key_formatted}:")
            output_lines.append(f"  {value}")
            output_lines.append("")
    
    return "\n".join(output_lines) if output_lines else colored("No valid content found", "red")

def print_agent_output(agent_name: str, output: Any):
    """Print agent output with specific colors and formatted content"""
    colors = {
        "PLANNER": "blue",
        "SERPER": "green",
        "SELECTOR": "magenta",
        "SCRAPER": "cyan",
        "REPORTER": "yellow"  # Added unique color for reporter
    }
    
    print("\n" + "="*50)
    print(colored(f"[{agent_name} AGENT]", colors[agent_name], attrs=['bold']))
    print(colored("-"*50, colors[agent_name]))
    
    if agent_name in ["PLANNER", "SELECTOR", "SCRAPER", "REPORTER"]:
        parsed_content = parse_agent_response(agent_name, output)
        formatted_output = format_parsed_content(parsed_content)
    else:
        formatted_output = json.dumps(output, indent=2) if isinstance(output, dict) else str(output)
        
    print(colored(formatted_output, colors[agent_name]))
    print(colored("="*50 + "\n", colors[agent_name]))

def update_state(state: AgentGraph, key: str, value: Any) -> AgentGraph:
    return {**state, key: value}

def planner_agent(state: AgentGraph) -> AgentGraph:
    user_query = state.get("research_question")
    reviewer_responses: List[str] = state.get("reviewer_response", [])
    feedback = reviewer_responses[-1] if reviewer_responses else ""
    
    prompt = planner_prompt_template.format(
        datetime=get_current_time_and_date(),
        feedback=feedback
    )
    
    messages = [
        {"role": "system", "content": f"{prompt}"},
        {"role": "user", "content": f"question {user_query}"}
    ]
    
    groq = GroqJsonModel()
    response = groq.invoke(messages)
    print_agent_output("PLANNER", response)
    return update_state(state, "planner_response", response)

def serper_tool(state: AgentGraph) -> AgentGraph:
    planner_response = state.get("planner_response")[-1].content
    planner_response = json.loads(planner_response)
    query = planner_response['search_term']
    serper_response = serpapi_search(query)
    
    print_agent_output("SERPER", serper_response)
    return update_state(state, "serper_response", serper_response)

def selector_agent(state: AgentGraph) -> AgentGraph:
    reviewer_responses: List[str] = state.get("reviewer_response", [])
    feedback = reviewer_responses[-1] if reviewer_responses else ""
    research_question = state.get("research_question")
    serp = state.get("serper_response")[-1]
    previous_selections = state.get("selector_response", [])
    
    prompt = selector_prompt_template.format(
        serp=serp,
        feedback=feedback,
        previous_selections=previous_selections,
        datetime=get_current_time_and_date()
    )
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"question {research_question}"}
    ]
    
    groq = GroqJsonModel()
    response = groq.invoke(messages)
    print_agent_output("SELECTOR", response)
    return update_state(state, "selector_response", response)



def scraper_agent(state: AgentGraph) -> AgentGraph:

    selector_responses = state.get('selector_response', [])
    if not selector_responses:
        error_response = {'error': 'No selector response found'}
        print_agent_output("SCRAPER", error_response)
        return {**state, 'scraper_response': [error_response]}

    last_selector_response = selector_responses[-1].content
    last_selector_response = json.loads(last_selector_response)
    url_to_scrape = last_selector_response.get('selected_page_url')
    
    
    if not url_to_scrape:
        error_response = {'error': 'No URL found in the last selector response'}
        print_agent_output("SCRAPER", error_response)
        return {**state, 'scraper_response': [error_response]}
        
    # Scrape the URL
    scraped_content = scrape_url(url_to_scrape)
    # print("Scraper agent :",scraped_content,sep="\n")
    print_agent_output("SCRAPER", scraped_content)
    
    return update_state(state, "scraper_response", scraped_content)


def reporter_agent(state: AgentGraph) -> AgentGraph:
    scraper_responses = state.get('scraper_response', [])
    if not scraper_responses:
        raise ValueError("Scraper response is empty. Cannot proceed with Reporter agent.")
    else:
        research = scraper_responses[-1].content
    reviewer_responses: List[str] = state.get("reviewer_response", [])
    feedback = reviewer_responses[-1] if reviewer_responses else ""
    research_question = state.get("research_question")
    reporter_responses = state.get("reporter_response", [])
    previous_reports = "".join([json.loads(report.content) for report in reporter_responses]) if reporter_responses else ""
    prompt = reporter_prompt_template.format(
        research=research,
        feedback=feedback,
        previous_reports=previous_reports,
        datetime=get_current_time_and_date()
    )
    print("Reporter prompt : ",prompt,sep="\n")
    messages = [
        {"role": "system", "content": f"""{prompt}"""},
        {"role": "user", "content": f"question {research_question}"}
    ]
    print("Reporter messages : ",messages,sep="\n")
    groq = GroqModel()
    response = groq.invoke(messages)
    print_agent_output("REPORTER", response)
    return update_state(state, "reporter_response", response)


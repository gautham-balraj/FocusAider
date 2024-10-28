from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class AgentGraph(TypedDict):
    research_question: str ## user query to the agent 
    planner_response: Annotated[list, add_messages] # provides the query to search in web   
    selector_response: Annotated[list, add_messages]  # selected URL for further scrapping 
    reporter_response: Annotated[list, add_messages]  
    reviewer_response: Annotated[list, add_messages]
    router_response: Annotated[list, add_messages]
    serper_response: Annotated[list, add_messages]
    scraper_response: Annotated[list, add_messages]
    final_reports: Annotated[list, add_messages]
    end_chain: Annotated[list, add_messages]



state = {
    "research_question":"",
    "planner_response": [],
    "selector_response": [],
    "reporter_response": [],
    "reviewer_response": [],
    "router_response": [],
    "serper_response": [],
    "scraper_response": [],
    "final_reports": [],
    "end_chain": []
}
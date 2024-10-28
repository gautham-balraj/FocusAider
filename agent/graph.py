from agents import planner_agent, serper_tool, selector_agent,scraper_agent,reporter_agent
from state import AgentGraph,state
from langgraph.graph import StateGraph, END



workflow  = StateGraph(AgentGraph)
workflow.add_node("planner_agent", planner_agent)
workflow.add_node("serper_tool", serper_tool)
workflow.add_node("selector_agent", selector_agent)
workflow.add_node("scraper_agent", scraper_agent)
workflow.add_node("reporter_agent", reporter_agent)
workflow.set_entry_point("planner_agent")
workflow.add_edge("planner_agent", "serper_tool")
workflow.add_edge("serper_tool", "selector_agent")
workflow.add_edge("selector_agent", "scraper_agent")
workflow.add_edge("scraper_agent", "reporter_agent")
workflow.add_edge("reporter_agent", END)


graph = workflow.compile()

iterations = 10

if __name__ == "__main__":

    verbose = False

    while True:
        print("Please enter your research question: what is LLM?")
        query = "What is computer use realeased by anthropic" 
        if query.lower() == "exit":
            break

        dict_inputs = {"research_question": query}
        # thread = {"configurable": {"thread_id": "4"}}
        limit = {"recursion_limit": iterations}

        # for event in workflow.stream(
        #     dict_inputs, thread, limit, stream_mode="values"
        #     ):
        #     if verbose:
        #         print("\nState Dictionary:", event)
        #     else:
        #         print("\n")

        for event in graph.stream(
            dict_inputs, limit):
            c = input("Do you want to continue? (y/n): ")
            if c.lower() == "n":
                break  # Break the inner loop
            if verbose:
                print("\nState Dictionary:", event)
            else:
                print("\n")
        if c.lower() == "n":
            break  # Break the outer loop if c was 'n'

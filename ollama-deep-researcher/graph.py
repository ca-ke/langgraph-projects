from dataclasses import replace
import json
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
from langgraph.utils.runnable import RunnableCallable
from configuration import Configuration
from state import SummaryState, SummaryStateInput, SummaryStateOutput
from prompt_loader import load_prompt, format, load_variables
from langchain_ollama import ChatOllama
from duck_duck_go_search import execute
from utils import remove_duplicates, get_content_from


def generate_query(
    state: SummaryStateInput,
    config: RunnableConfig,
) -> SummaryState:
    query_writer_instructions = format(
        load_variables(
            load_prompt("prompts/query_writer_agent_prompt.yaml"),
            variables={"research_topic": f"{state.research_topic}"},
        )
    )

    configuration = Configuration.from_runnable_config(config)
    llm_json_mode = ChatOllama(
        base_url=configuration.ollama_base_url,
        model=configuration.ollama_model,
        temperature=0,
        format="json",
    )
    messages = [
        SystemMessage(content=query_writer_instructions),
        HumanMessage(content="Generate a query for web search"),
    ]
    result = llm_json_mode.invoke(messages)
    query = json.loads(result.content)

    return SummaryState(search_query=query["query"])


def web_research(
    state: SummaryState,
    config: RunnableConfig,
) -> SummaryState:
    results = execute(query=state.search_query, max_results=3, fetch_full_page=False)
    sites = remove_duplicates(results)
    content = get_content_from(data=results, using=sites)

    return replace(
        state,
        search_query=state.search_query,
        research_loop_count=state.research_loop_count + 1,
        web_search_results=[content],
        sources_gathered=sites,
    )


def summarize_sources(
    state: SummaryState,
    config: RunnableConfig,
) -> SummaryState:
    existing_summary = state.running_summary
    most_recent_web_research = state.web_search_results[-1]
    summarizer_instructions = format(
        load_prompt("prompts/summarizer_agent_prompt.yaml")
    )

    if existing_summary:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Existing Summary> \n {existing_summary} \n <Existing Summary>\n\n"
            f"<New Search Results> \n {most_recent_web_research} \n <New Search Results>"
        )
    else:
        human_message_content = (
            f"<User Input> \n {state.research_topic} \n <User Input>\n\n"
            f"<Search Results> \n {most_recent_web_research} \n <Search Results>"
        )

    configuration = Configuration.from_runnable_config(config)
    llm = ChatOllama(
        base_url=configuration.ollama_base_url,
        model=configuration.ollama_model,
        temperature=0,
    )
    result = llm.invoke(
        [
            SystemMessage(content=summarizer_instructions),
            HumanMessage(content=human_message_content),
        ]
    )

    running_summary = result.content

    return replace(state, running_summary=running_summary)


def finalize_summary(state: SummaryState, config: RunnableConfig) -> SummaryStateOutput:
    all_sources = "\n".join(source for source in state.sources_gathered)
    state.running_summary = (
        f"## Summary:\n\n{state.running_summary}\n\n ### Sources: \n\n {all_sources}"
    )

    return SummaryStateOutput(running_summary=state.running_summary)


def reflect(
    state: SummaryState,
    config: RunnableConfig,
) -> SummaryState:
    reflection_instruction = format(
        load_variables(
            load_prompt("prompts/reflection_agent_prompt.yaml"),
            variables={"research_topic": f"{state.research_topic}"},
        )
    )
    configuration = Configuration.from_runnable_config(config)
    llm_json_mode = ChatOllama(
        base_url=configuration.ollama_base_url,
        model=configuration.ollama_model,
        temperature=0,
        format="json",
    )
    result = llm_json_mode.invoke(
        [
            SystemMessage(content=reflection_instruction),
            HumanMessage(
                content=f"Identify a knowledge gap and generate a follow-up web search query based on our existing knowledge: {state.running_summary}"
            ),
        ]
    )
    follow_up_query = json.loads(result.content)
    query = follow_up_query.get("follow_up_query")

    if not query:
        return replace(
            state, search_query=f"Tell me more about: {state.research_topic}"
        )
    return replace(state, search_query=follow_up_query["follow_up_query"])


def route_search(
    state: SummaryState,
    config: RunnableConfig,
) -> Literal["finalize_summary", "web_research"]:
    configuration = Configuration.from_runnable_config(config)
    if state.research_loop_count <= configuration.max_web_research_loops:
        return "web_research"
    return "finalize_summary"


def build_graph(research_topic: str):
    builder = StateGraph(
        SummaryState,
        input=SummaryStateInput,
        output=SummaryStateOutput,
        config_schema=Configuration,
    )
    builder.add_node("generate_query", generate_query)
    builder.add_node("web_research", web_research)
    builder.add_node("summarize_sources", summarize_sources)
    builder.add_node("finalize_summary", finalize_summary)
    builder.add_node("reflect", reflect)

    builder.add_edge(START, "generate_query")
    builder.add_edge("generate_query", "web_research")
    builder.add_edge("web_research", "summarize_sources")
    builder.add_edge("summarize_sources", "reflect")
    builder.add_conditional_edges("reflect", route_search)
    builder.add_edge("finalize_summary", END)

    graph = builder.compile()
    return graph.invoke(SummaryStateInput(research_topic=research_topic))[
        "running_summary"
    ]

"""
DevDocsAI V2 — LangGraph Orchestrator Agent
=============================================
Central coordinator that manages the multi-agent workflow as a
LangGraph StateGraph. Routes queries to specialized agents based
on complexity classification, manages parallel execution, and
controls the reflection loop.

Execution Modes:
    - V1 Fast Path: Simple queries bypass agents entirely (zero overhead)
    - V2 Full Pipeline: Complex queries go through planning → retrieval → reflection

LangGraph State Diagram:
    START → classify_query
        → [simple] → v1_fast_path → END
        → [complex] → plan_query → execute_agents → aggregate → reflect
            → [pass] → END
            → [fail, count < max] → re_retrieve → aggregate → reflect
            → [fail, count >= max] → END

References:
    docs/README_V2_ARCHITECTURE.md §5.1 (Orchestrator Agent)
    docs/README_V2_ARCHITECTURE.md §7 (Agent Decision Matrix)
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional

from langgraph.graph import END, StateGraph

from app.agents.base import BaseAgent
from app.agents.llm_provider import get_agent_llm
from app.agents.schemas import (
    AgentOutput,
    AgentStep,
    OrchestratorState,
    ReasoningTrace,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Query Classification Keywords ────────────────────────────────────────────

_ARCHITECTURE_KEYWORDS = frozenset({
    "architecture", "design", "structure", "overview", "diagram", "dependency",
    "component", "module", "layer", "pattern", "flow", "relationship",
    "import", "inheritance", "coupling",
})

_DOCUMENTATION_KEYWORDS = frozenset({
    "readme", "document", "documentation", "api doc", "onboard", "guide",
    "tutorial", "wiki", "explain the project",
})

_CODE_REVIEW_KEYWORDS = frozenset({
    "review", "optimize", "refactor", "performance", "security", "vulnerability",
    "bug", "smell", "improve", "best practice", "anti-pattern",
})

_COMPLEXITY_INDICATORS = frozenset({
    "how does", "explain", "trace", "walk through", "step by step",
    "end to end", "e2e", "entire", "complete", "all", "compare",
    "difference", "relationship between", "interact",
})


def classify_query(query: str) -> str:
    """
    Classify a user query into a routing category.

    Returns one of:
        "simple", "general_code", "architecture",
        "documentation", "code_review", "complex_multi_hop"
    """
    q = query.lower().strip()
    words = set(q.split())

    # Check for complexity indicators first
    is_complex = any(indicator in q for indicator in _COMPLEXITY_INDICATORS)

    # Architecture queries
    if words & _ARCHITECTURE_KEYWORDS:
        return "complex_multi_hop" if is_complex else "architecture"

    # Documentation queries
    if words & _DOCUMENTATION_KEYWORDS:
        return "documentation"

    # Code review queries
    if words & _CODE_REVIEW_KEYWORDS:
        return "code_review"

    # Complex multi-hop (long questions with complexity indicators)
    if is_complex and len(q.split()) > 8:
        return "complex_multi_hop"

    # Short, direct questions → simple (V1 fast path)
    if len(q.split()) <= 6 and not is_complex:
        return "simple"

    return "general_code"


# ── Agent Decision Matrix ────────────────────────────────────────────────────

# Maps query_type → list of agents to invoke (in order)
AGENT_DECISION_MATRIX: Dict[str, List[str]] = {
    "simple": [],  # V1 fast path — no agents
    "general_code": ["planning", "retrieval", "reflection"],
    "architecture": ["planning", "repository", "retrieval", "architecture", "reflection"],
    "documentation": ["planning", "repository", "retrieval", "documentation", "reflection"],
    "code_review": ["planning", "retrieval", "code_analysis", "reflection"],
    "complex_multi_hop": [
        "planning", "repository", "retrieval", "architecture",
        "code_analysis", "reflection",
    ],
}


# ── Orchestrator Node Functions ──────────────────────────────────────────────

async def node_classify_query(state: OrchestratorState) -> Dict[str, Any]:
    """Classify the query and determine which agents to invoke."""
    query = state.get("query", "")
    mode = state.get("mode", "auto")

    if mode == "v1":
        query_type = "simple"
    elif mode == "v2":
        query_type = classify_query(query)
        if query_type == "simple":
            query_type = "general_code"  # Force V2 path
    else:
        query_type = classify_query(query)

    logger.info("Query classified", query_type=query_type, query_preview=query[:80])
    return {
        "query_type": query_type,
        "agent_confidences": {},
        "reflection_count": 0,
        "retrieval_results": [],
        "sources": [],
        "reasoning_trace": ReasoningTrace(
            steps=[
                AgentStep(
                    agent_name="orchestrator",
                    action=f"Classified query as '{query_type}'",
                    confidence=1.0,
                    output_summary=f"Query type: {query_type}",
                )
            ]
        ).model_dump(),
    }


async def node_v1_fast_path(state: OrchestratorState) -> Dict[str, Any]:
    """
    Execute the V1 chat pipeline directly (no agent overhead).
    Wraps the existing ChatService.chat() for simple queries.
    """
    start = time.perf_counter()
    try:
        from app.services.chat.chat_service import ChatService

        chat_service = ChatService()
        result = await chat_service.chat(
            repo_id=state["repo_id"],
            question=state["query"],
            conversation_history=state.get("conversation_history", []),
        )

        duration_ms = int((time.perf_counter() - start) * 1000)
        sources = result.get("sources", [])

        trace = state.get("reasoning_trace", {})
        steps = trace.get("steps", []) if isinstance(trace, dict) else []
        steps.append(AgentStep(
            agent_name="v1_fast_path",
            action="Executed V1 Hybrid RAG pipeline directly",
            tools_invoked=["hybrid_retriever"],
            confidence=0.8,
            duration_ms=duration_ms,
            output_summary=f"V1 response generated ({len(result.get('answer', ''))} chars)",
        ).model_dump())

        return {
            "final_answer": result.get("answer", ""),
            "sources": sources,
            "reasoning_trace": {
                "steps": steps,
                "total_duration_ms": duration_ms,
                "total_tokens_used": 0,
                "agents_invoked": ["v1_fast_path"],
                "reflection_cycles": 0,
                "final_confidence": 0.8,
            },
        }

    except Exception as e:
        logger.error("V1 fast path failed", error=str(e))
        return {
            "final_answer": f"I encountered an error: {str(e)}",
            "error": str(e),
        }


async def node_plan_query(state: OrchestratorState) -> Dict[str, Any]:
    """Invoke the Planning Agent to decompose the query."""
    from app.agents.planning_agent import PlanningAgent

    agent = PlanningAgent(llm=get_agent_llm())
    output = await agent.run(state)

    # Store plan in state
    plan = output.result if output.result else None

    trace = state.get("reasoning_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    steps.append(AgentStep(
        agent_name="planning",
        action=output.reasoning_summary or "Generated execution plan",
        tools_invoked=output.tools_used,
        confidence=output.confidence,
        duration_ms=output.duration_ms,
        output_summary=output.reasoning_summary,
    ).model_dump())

    confidences = state.get("agent_confidences", {})
    confidences["planning"] = output.confidence

    return {
        "execution_plan": plan.model_dump() if hasattr(plan, "model_dump") else plan,
        "agent_confidences": confidences,
        "reasoning_trace": {**trace, "steps": steps},
    }


async def node_gather_repo_context(state: OrchestratorState) -> Dict[str, Any]:
    """Invoke the Repository Agent to gather context."""
    from app.agents.repository_agent import RepositoryAgent

    agent = RepositoryAgent()
    output = await agent.run(state)

    trace = state.get("reasoning_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    steps.append(AgentStep(
        agent_name="repository",
        action=output.reasoning_summary or "Gathered repository context",
        tools_invoked=output.tools_used,
        confidence=output.confidence,
        duration_ms=output.duration_ms,
        output_summary=output.reasoning_summary,
    ).model_dump())

    confidences = state.get("agent_confidences", {})
    confidences["repository"] = output.confidence

    return {
        "repo_context": output.result.model_dump() if hasattr(output.result, "model_dump") else output.result,
        "agent_confidences": confidences,
        "reasoning_trace": {**trace, "steps": steps},
    }


async def node_execute_retrieval(state: OrchestratorState) -> Dict[str, Any]:
    """Invoke the Retrieval Agent for multi-step retrieval."""
    from app.agents.retrieval_agent import RetrievalAgent

    agent = RetrievalAgent()
    output = await agent.run(state)

    retrieval_results = output.result if isinstance(output.result, list) else []

    # Build source references from results
    sources = []
    seen = set()
    for r in retrieval_results[:15]:
        meta = r.get("metadata", {}) if isinstance(r, dict) else {}
        file_path = meta.get("file", "")
        name = meta.get("name", "")
        if file_path and (file_path, name) not in seen:
            seen.add((file_path, name))
            sources.append({
                "file": file_path,
                "function": name if meta.get("type") in ("function", "method") else None,
                "line_start": meta.get("line_start"),
                "line_end": meta.get("line_end"),
                "content_preview": r.get("content", "")[:150] if isinstance(r, dict) else "",
                "score": r.get("score", 0.0) if isinstance(r, dict) else 0.0,
            })

    trace = state.get("reasoning_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    steps.append(AgentStep(
        agent_name="retrieval",
        action=output.reasoning_summary or "Executed retrieval",
        tools_invoked=output.tools_used,
        confidence=output.confidence,
        duration_ms=output.duration_ms,
        output_summary=f"Retrieved {len(retrieval_results)} results",
    ).model_dump())

    confidences = state.get("agent_confidences", {})
    confidences["retrieval"] = output.confidence

    return {
        "retrieval_results": retrieval_results,
        "sources": sources,
        "agent_confidences": confidences,
        "reasoning_trace": {**trace, "steps": steps},
    }


async def node_execute_architecture(state: OrchestratorState) -> Dict[str, Any]:
    """Invoke the Architecture Agent if needed."""
    from app.agents.architecture_agent import ArchitectureAgent

    agent = ArchitectureAgent()
    output = await agent.run(state)

    trace = state.get("reasoning_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    steps.append(AgentStep(
        agent_name="architecture",
        action=output.reasoning_summary or "Analyzed architecture",
        tools_invoked=output.tools_used,
        confidence=output.confidence,
        duration_ms=output.duration_ms,
        output_summary=output.reasoning_summary,
    ).model_dump())

    confidences = state.get("agent_confidences", {})
    confidences["architecture"] = output.confidence

    return {
        "architecture_context": output.result if isinstance(output.result, str) else str(output.result or ""),
        "agent_confidences": confidences,
        "reasoning_trace": {**trace, "steps": steps},
    }


async def node_execute_documentation(state: OrchestratorState) -> Dict[str, Any]:
    """Invoke the Documentation Agent if needed."""
    from app.agents.documentation_agent import DocumentationAgent

    agent = DocumentationAgent(llm=get_agent_llm())
    output = await agent.run(state)

    trace = state.get("reasoning_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    steps.append(AgentStep(
        agent_name="documentation",
        action=output.reasoning_summary or "Generated documentation",
        tools_invoked=output.tools_used,
        confidence=output.confidence,
        duration_ms=output.duration_ms,
        output_summary=output.reasoning_summary,
    ).model_dump())

    confidences = state.get("agent_confidences", {})
    confidences["documentation"] = output.confidence

    return {
        "documentation_output": output.result if isinstance(output.result, str) else str(output.result or ""),
        "agent_confidences": confidences,
        "reasoning_trace": {**trace, "steps": steps},
    }


async def node_execute_code_analysis(state: OrchestratorState) -> Dict[str, Any]:
    """Invoke the Code Analysis Agent if needed."""
    from app.agents.code_analysis_agent import CodeAnalysisAgent

    agent = CodeAnalysisAgent(llm=get_agent_llm())
    output = await agent.run(state)

    trace = state.get("reasoning_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    steps.append(AgentStep(
        agent_name="code_analysis",
        action=output.reasoning_summary or "Analyzed code",
        tools_invoked=output.tools_used,
        confidence=output.confidence,
        duration_ms=output.duration_ms,
        output_summary=output.reasoning_summary,
    ).model_dump())

    confidences = state.get("agent_confidences", {})
    confidences["code_analysis"] = output.confidence

    return {
        "code_analysis_output": output.result if isinstance(output.result, str) else str(output.result or ""),
        "agent_confidences": confidences,
        "reasoning_trace": {**trace, "steps": steps},
    }


async def node_aggregate(state: OrchestratorState) -> Dict[str, Any]:
    """
    Aggregate all agent outputs and generate the final answer using LLM.
    """
    start = time.perf_counter()
    llm = get_agent_llm()

    # Build context from all agent outputs
    context_parts = []

    # Repository context
    repo_ctx = state.get("repo_context")
    if repo_ctx and isinstance(repo_ctx, dict):
        context_parts.append(
            f"**Repository Context:**\n"
            f"- Language: {repo_ctx.get('primary_language', 'unknown')}\n"
            f"- Framework: {repo_ctx.get('framework', 'unknown')}\n"
            f"- Architecture: {repo_ctx.get('architecture_type', 'unknown')}\n"
            f"- Summary: {repo_ctx.get('summary', '')[:500]}\n"
        )

    # Retrieval results
    results = state.get("retrieval_results", [])
    if results:
        context_parts.append("**Retrieved Code Context:**")
        for i, r in enumerate(results[:15]):
            if isinstance(r, dict):
                meta = r.get("metadata", {})
                name = meta.get("name", "")
                file_path = meta.get("file", "")
                header = f"[Source {i+1}]"
                if name:
                    header += f" {name}"
                if file_path:
                    header += f" ({file_path})"
                header += f" [score: {r.get('score', 0):.2f}]"
                context_parts.append(f"{header}\n{r.get('content', '')[:600]}")

    # Architecture context
    arch_ctx = state.get("architecture_context")
    if arch_ctx:
        context_parts.append(f"**Architecture Analysis:**\n{arch_ctx[:1000]}")

    # Documentation output
    doc_output = state.get("documentation_output")
    if doc_output:
        context_parts.append(f"**Documentation:**\n{doc_output[:1000]}")

    # Code analysis output
    code_output = state.get("code_analysis_output")
    if code_output:
        context_parts.append(f"**Code Analysis:**\n{code_output[:1000]}")

    full_context = "\n\n---\n\n".join(context_parts)

    # Generate final answer
    system_prompt = (
        "You are DevDocsAI, an expert AI Software Intelligence Platform. "
        "You deeply understand software repositories through multi-agent analysis.\n\n"
        "You have received context from multiple specialized agents:\n"
        "- Repository Agent: project metadata and structure\n"
        "- Retrieval Agent: relevant code chunks via hybrid search\n"
        "- Architecture Agent: dependency graphs and structural analysis\n"
        "- Code Analysis Agent: code review and optimization insights\n\n"
        "Guidelines:\n"
        "- Answer based ONLY on the provided context\n"
        "- Include specific file paths and line numbers\n"
        "- Use markdown formatting for readability\n"
        "- If information is insufficient, say so clearly\n"
        "- Never hallucinate code or functionality\n"
        "- Provide a comprehensive, well-structured answer"
    )

    # Build conversation with history
    messages = [{"role": "system", "content": system_prompt}]
    history = state.get("conversation_history", [])
    if history:
        messages.extend(history[-6:])

    user_prompt = (
        f"Multi-Agent Analysis Context:\n\n{full_context}\n\n"
        f"---\n\nQuestion: {state.get('query', '')}\n\n"
        f"Provide a comprehensive answer based on the analysis above."
    )
    messages.append({"role": "user", "content": user_prompt})

    try:
        answer = await llm.generate(messages, temperature=0.1, max_tokens=4096)
    except Exception as e:
        logger.error("Final answer generation failed", error=str(e))
        answer = f"I encountered an error generating the response: {str(e)}"

    duration_ms = int((time.perf_counter() - start) * 1000)

    trace = state.get("reasoning_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    steps.append(AgentStep(
        agent_name="aggregator",
        action="Aggregated agent outputs and generated final answer",
        tools_invoked=["llm_generate"],
        confidence=0.9,
        duration_ms=duration_ms,
        output_summary=f"Generated answer ({len(answer)} chars)",
    ).model_dump())

    return {
        "final_answer": answer,
        "reasoning_trace": {**trace, "steps": steps},
    }


async def node_reflect(state: OrchestratorState) -> Dict[str, Any]:
    """Invoke the Reflection Agent to validate the response."""
    from app.agents.reflection_agent import ReflectionAgent

    agent = ReflectionAgent(llm=get_agent_llm())
    output = await agent.run(state)

    reflection = output.result
    reflection_dict = reflection.model_dump() if hasattr(reflection, "model_dump") else (reflection or {})

    trace = state.get("reasoning_trace", {})
    steps = trace.get("steps", []) if isinstance(trace, dict) else []
    steps.append(AgentStep(
        agent_name="reflection",
        action=output.reasoning_summary or "Validated response",
        tools_invoked=output.tools_used,
        confidence=output.confidence,
        duration_ms=output.duration_ms,
        output_summary=output.reasoning_summary,
    ).model_dump())

    confidences = state.get("agent_confidences", {})
    confidences["reflection"] = output.confidence

    count = state.get("reflection_count", 0) + 1

    # Calculate final confidence
    final_conf = BaseAgent.calculate_final_confidence(confidences)

    # Update trace totals
    total_duration = sum(s.get("duration_ms", 0) for s in steps)
    agents_invoked = list({s.get("agent_name", "") for s in steps})

    return {
        "reflection_result": reflection_dict,
        "reflection_count": count,
        "agent_confidences": confidences,
        "reasoning_trace": {
            "steps": steps,
            "total_duration_ms": total_duration,
            "total_tokens_used": 0,
            "agents_invoked": agents_invoked,
            "reflection_cycles": count,
            "final_confidence": final_conf,
        },
    }


# ── Conditional Edge Functions ───────────────────────────────────────────────

def should_use_v1_fast_path(state: OrchestratorState) -> str:
    """Route to V1 fast path or V2 planning."""
    if state.get("query_type") == "simple":
        return "v1_fast_path"
    return "plan_query"


def should_invoke_architecture(state: OrchestratorState) -> str:
    """Check if Architecture Agent is needed."""
    query_type = state.get("query_type", "")
    plan = state.get("execution_plan")
    needs_arch = False

    if isinstance(plan, dict):
        needs_arch = plan.get("requires_architecture", False)

    if query_type in ("architecture", "complex_multi_hop") or needs_arch:
        return "execute_architecture"
    return "skip_architecture"


def should_invoke_documentation(state: OrchestratorState) -> str:
    """Check if Documentation Agent is needed."""
    if state.get("query_type") == "documentation":
        return "execute_documentation"
    return "skip_documentation"


def should_invoke_code_analysis(state: OrchestratorState) -> str:
    """Check if Code Analysis Agent is needed."""
    query_type = state.get("query_type", "")
    plan = state.get("execution_plan")
    needs_code = False

    if isinstance(plan, dict):
        needs_code = plan.get("requires_code_analysis", False)

    if query_type in ("code_review", "complex_multi_hop") or needs_code:
        return "execute_code_analysis"
    return "skip_code_analysis"


def should_re_retrieve(state: OrchestratorState) -> str:
    """Check if re-retrieval is needed based on reflection."""
    reflection = state.get("reflection_result")
    count = state.get("reflection_count", 0)
    max_cycles = settings.agent_max_reflection_cycles

    if not reflection:
        return "end"

    passed = reflection.get("passed", True) if isinstance(reflection, dict) else True
    confidence = reflection.get("confidence", 1.0) if isinstance(reflection, dict) else 1.0

    if not passed and count < max_cycles and confidence < settings.agent_confidence_threshold:
        logger.info(
            "Re-retrieval triggered",
            reflection_cycle=count,
            confidence=confidence,
        )
        return "re_retrieve"

    return "end"


async def _passthrough(state: OrchestratorState) -> Dict[str, Any]:
    """No-op node used as a branching point in the graph."""
    return {}


# ── Build the LangGraph Workflow ─────────────────────────────────────────────

def build_orchestrator_graph() -> StateGraph:
    """
    Construct the LangGraph StateGraph for the multi-agent orchestrator.

    Graph:
        START → classify_query
            → [simple] → v1_fast_path → END
            → [complex] → plan_query → gather_repo_context → execute_retrieval
                → (optional) execute_architecture
                → (optional) execute_documentation
                → (optional) execute_code_analysis
                → aggregate → reflect
                    → [pass] → END
                    → [fail] → re_retrieve → aggregate → reflect → ...
    """
    workflow = StateGraph(OrchestratorState)

    # Add nodes
    workflow.add_node("classify_query", node_classify_query)
    workflow.add_node("v1_fast_path", node_v1_fast_path)
    workflow.add_node("plan_query", node_plan_query)
    workflow.add_node("gather_repo_context", node_gather_repo_context)
    workflow.add_node("execute_retrieval", node_execute_retrieval)
    workflow.add_node("execute_architecture", node_execute_architecture)
    workflow.add_node("execute_documentation", node_execute_documentation)
    workflow.add_node("execute_code_analysis", node_execute_code_analysis)
    workflow.add_node("aggregate", node_aggregate)
    workflow.add_node("reflect", node_reflect)

    # Entry point
    workflow.set_entry_point("classify_query")

    # Classify → V1 or V2
    workflow.add_conditional_edges(
        "classify_query",
        should_use_v1_fast_path,
        {
            "v1_fast_path": "v1_fast_path",
            "plan_query": "plan_query",
        },
    )

    # V1 fast path → END
    workflow.add_edge("v1_fast_path", END)

    # V2 pipeline: plan → repo context → retrieval
    workflow.add_edge("plan_query", "gather_repo_context")
    workflow.add_edge("gather_repo_context", "execute_retrieval")

    # After retrieval → check if architecture is needed
    workflow.add_conditional_edges(
        "execute_retrieval",
        should_invoke_architecture,
        {
            "execute_architecture": "execute_architecture",
            "skip_architecture": "check_documentation",
        },
    )

    # After architecture → check documentation
    # We need a pass-through node for the skip case
    workflow.add_node("check_documentation", _passthrough)
    workflow.add_conditional_edges(
        "execute_architecture",
        should_invoke_documentation,
        {
            "execute_documentation": "execute_documentation",
            "skip_documentation": "check_code_analysis",
        },
    )
    workflow.add_conditional_edges(
        "check_documentation",
        should_invoke_documentation,
        {
            "execute_documentation": "execute_documentation",
            "skip_documentation": "check_code_analysis",
        },
    )

    # After documentation → check code analysis
    workflow.add_node("check_code_analysis", _passthrough)
    workflow.add_conditional_edges(
        "execute_documentation",
        should_invoke_code_analysis,
        {
            "execute_code_analysis": "execute_code_analysis",
            "skip_code_analysis": "aggregate",
        },
    )
    workflow.add_conditional_edges(
        "check_code_analysis",
        should_invoke_code_analysis,
        {
            "execute_code_analysis": "execute_code_analysis",
            "skip_code_analysis": "aggregate",
        },
    )

    # Code analysis → aggregate
    workflow.add_edge("execute_code_analysis", "aggregate")

    # Aggregate → reflect
    workflow.add_edge("aggregate", "reflect")

    # Reflect → end or re-retrieve
    workflow.add_conditional_edges(
        "reflect",
        should_re_retrieve,
        {
            "end": END,
            "re_retrieve": "execute_retrieval",
        },
    )

    return workflow


# ── Compiled Graph (singleton) ───────────────────────────────────────────────

_compiled_graph = None


def get_orchestrator():
    """Get the compiled orchestrator graph (singleton)."""
    global _compiled_graph
    if _compiled_graph is None:
        workflow = build_orchestrator_graph()
        _compiled_graph = workflow.compile()
    return _compiled_graph


async def run_agent_pipeline(
    repo_id: str,
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    mode: str = "auto",
) -> Dict[str, Any]:
    """
    Main entry point for the V2 agent pipeline.

    Args:
        repo_id: Repository identifier
        query: User's question
        conversation_history: Previous messages for context
        mode: "auto" | "v2" | "v1"

    Returns:
        Dict with final_answer, sources, reasoning_trace, confidence
    """
    graph = get_orchestrator()

    initial_state: OrchestratorState = {
        "query": query,
        "repo_id": repo_id,
        "conversation_history": conversation_history or [],
        "mode": mode,
        "query_type": "",
        "repo_context": None,
        "execution_plan": None,
        "retrieval_results": [],
        "architecture_context": None,
        "documentation_output": None,
        "code_analysis_output": None,
        "agent_confidences": {},
        "reflection_result": None,
        "reflection_count": 0,
        "final_answer": "",
        "sources": [],
        "reasoning_trace": {},
        "error": None,
    }

    try:
        final_state = await graph.ainvoke(initial_state)

        return {
            "answer": final_state.get("final_answer", ""),
            "sources": final_state.get("sources", []),
            "reasoning_trace": final_state.get("reasoning_trace", {}),
            "confidence": final_state.get("reasoning_trace", {}).get("final_confidence", 0.5),
            "agents_invoked": final_state.get("reasoning_trace", {}).get("agents_invoked", []),
            "query_type": final_state.get("query_type", "unknown"),
            "error": final_state.get("error"),
        }

    except Exception as e:
        logger.error("Agent pipeline failed, falling back to V1", error=str(e), exc_info=True)
        # Graceful degradation: fall back to V1
        try:
            from app.services.chat.chat_service import ChatService
            chat_service = ChatService()
            v1_result = await chat_service.chat(
                repo_id=repo_id,
                question=query,
                conversation_history=conversation_history,
            )
            return {
                "answer": v1_result.get("answer", ""),
                "sources": v1_result.get("sources", []),
                "reasoning_trace": {
                    "steps": [{
                        "agent_name": "v1_fallback",
                        "action": f"Agent pipeline failed ({str(e)[:100]}), fell back to V1",
                        "confidence": 0.5,
                    }],
                    "final_confidence": 0.5,
                },
                "confidence": 0.5,
                "agents_invoked": ["v1_fallback"],
                "query_type": "simple",
                "error": f"V2 pipeline failed, used V1 fallback: {str(e)[:200]}",
            }
        except Exception as e2:
            return {
                "answer": f"I encountered an error processing your question: {str(e2)}",
                "sources": [],
                "reasoning_trace": {},
                "confidence": 0.0,
                "agents_invoked": [],
                "query_type": "error",
                "error": str(e2),
            }

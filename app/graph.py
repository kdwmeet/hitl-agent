from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

class AgentState(TypedDict):
    query: str
    category: str
    risk_level: str
    draft: str
    status: str
    feedback: str

def classifier_node(state: AgentState):
    """문의의 카테고리와 위험도를 분류합니다."""
    llm = ChatOpenAI(model="gpt-5-mini", reasoning_effort="low")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "고객 문의를 분류합니다. 결제 오류, 환불, 계정 정지, 불만족과 관련된 내용은 risk_level을 'HIGH'로 분류하고, 단순 정보 요청이나 일반 문의는 'LOW'로 분류하십시오. 출력은 반드시 '카테고리명|HIGH 또는 LOW' 형식으로 작성하십시오."),
        ("user", "{query}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"query": state["query"]}).content.split("|")
    
    category = response[0].strip()
    risk_level = response[1].strip() if len(response) > 1 else "LOW"
    
    return {"category": category, "risk_level": risk_level}

def drafter_node(state: AgentState):
    """분류 결과와 관리자 피드백을 바탕으로 답변 초안을 작성합니다."""
    llm = ChatOpenAI(model="gpt-5-mini", reasoning_effort="low")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "전문적인 비즈니스 고객 서비스 담당자로서 답변 초안을 작성하십시오. 관리자의 피드백(feedback)이 존재한다면, 기존 내용을 무시하고 피드백의 지시사항을 철저히 반영하여 초안을 재작성하십시오."),
        ("user", "문의 내용: {query}\n카테고리: {category}\n관리자 피드백: {feedback}")
    ])
    
    chain = prompt | llm
    feedback_text = state.get("feedback", "없음")
    
    draft = chain.invoke({
        "query": state["query"], 
        "category": state.get("category", ""),
        "feedback": feedback_text
    }).content
    
    return {"draft": draft}

def human_review_node(state: AgentState):
    """
    관리자 검토를 위한 더미 노드입니다. 
    이 노드에 도달하기 전(interrupt_before)에 그래프 실행이 중단되며, 
    이후 외부 UI(Streamlit)에서 상태를 업데이트하고 재개합니다.
    """
    pass

def execute_node(state: AgentState):
    """최종 처리 및 발송을 담당하는 노드입니다."""
    return {"status": "completed"}

def route_after_draft(state: AgentState):
    """위험도에 따라 관리자 검토 여부를 결정합니다."""
    if state.get("risk_level") == "HIGH":
        return "human_review"
    return "execute"

def route_after_review(state: AgentState):
    """관리자의 승인 여부에 따라 재작성 또는 실행 단계로 라우팅합니다."""
    if state.get("status") == "rejected":
        return "drafter"
    return "execute"

# 그래프 조립
workflow = StateGraph(AgentState)

workflow.add_node("classifier", classifier_node)
workflow.add_node("drafter", drafter_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("execute", execute_node)

workflow.add_edge(START, "classifier")
workflow.add_edge("classifier", "drafter")
workflow.add_conditional_edges("drafter", route_after_draft)
workflow.add_conditional_edges("human_review", route_after_review)
workflow.add_edge("execute", END)

# 메모리(체크포인터) 생성 및 그래프 컴파일
# human_review 노드 실행 직전에 시스템을 일시 정지하도록 설정합니다.
memory = MemorySaver()
app_graph = workflow.compile(
    checkpointer=memory, 
    interrupt_before=["human_review"]
)
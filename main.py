import streamlit as st
from app.graph import app_graph

st.set_page_config(page_title="HITL CS 에스컬레이션 에이전트", layout="wide")

st.title("HITL CS 에스컬레이션 에이전트")
st.caption("AI가 문의를 1차 처리하며, 고위험 문의는 관리자의 검토ㅡㄹ 거쳐 안전하게 응대합니다.")
st.divider()

# 세션 상태 초기화
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False

# 고객 문의 입력 영역
st.subheader("고객 문의 접수 시뮬레이션")
query = st.text_area("고객 문의 내용을 입력하십시오.", height=100)

if st.button("문의 접수 및 분석 시작", type="primary"):
    if query.strip():
        # 데모 목적상 새로운 문의마다 고유한 스레드 ID 생성
        st.session_state.thread_id = "ticket_" + str(hash(query))[-6:]
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        initial_state = {"query": query, "status": "pending", "feedback": ""}

        with st.spinner("AI가 문의를 분석하고 답변 초안을 작성하고 있습니다."):
            app_graph.invoke(initial_state, config)

        st.session_state.is_running = True
        st.rerun()

st.divider()

# 처리 상태 모니터링 및 개입 영역
if st.session_state.is_running and st.session_state.thread_id:
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # 현재 그래프의 상태(State)와 다음에 실행될 노드(Next) 정보를 가져옵니다.
    current_state = app_graph.get_state(config)
    state_values = current_state.values
    next_nodes = current_state.next

    if state_values:
        st.subheader("분석 및 처리 결과")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("분류 카테고리", value=state_values.get("category", ""), disabled=True)
        with col2:
            st.text_input("위험도 (Risk Level)", value=state_values.get("risk_level", ""), disabled=True)
        
        st.text_area("AI 작성 답변 초안", value=state_values.get("draft", ""), height= 200, disabled=True)

    # 그래프가 human_review 노드 앞에서 중단된 상태인지 확인합니다.
    if "human_review" in next_nodes:
        st.error("주의: 고위험 문의로 분류되어 프로세스가 일시 중지 되었습니다. 관리자의 검토 및 승인이 필요합니다.")
         
        feedback_input = st.text_input("반려 시 수정 지시사항을 입력하십시오.")

        action_col1, action_col2 = st.columns(2)

        # 승인 처리 로직
        if action_col1.button("초안 승인 및 발송 처리", use_container_width=True):
            # 상태를 업데이트하고, 중단점이었던 human_review 노드로 처리 결과를 전달
            app_graph.update_state(config, {"status": "qpproved"}, as_node="human_review")
            # 입력값 없이 None을 주어 그래프 마저 실행
            app_graph.invoke(None, config)
            st.rerun()

        # 반려 처리 로직
        if action_col2.button("초안 반려 및 재작성 지시", use_container_width=True):
            app_graph.update_state(config, {"status": "rejected", "feedback": feedback_input}, as_node="human_review")
            app_graph.invoke(None, config)
            st.rerun()

    # 실행 대기 중인 노드가 없다면 프로세스가 끝까지 완료된 것입니다.
    elif not next_nodes and state_values.get("status") == "completed":
        st.success("해당 문의 처리가 안전하게 완료되었습니다.")
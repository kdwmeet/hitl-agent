# HITL CS Escalation Agent (휴먼 인 더 루프 CS 에스컬레이션 에이전트)

## 1. 프로젝트 개요

HITL(Human-in-the-loop) CS 에스컬레이션 에이전트는 AI의 자동화 능력과 인간 관리자의 판단력을 결합한 안전한 고객 응대 시스템입니다.

단순 정보성 문의는 AI가 즉시 처리하여 업무 효율을 높이고, 환불, 계정 정지, 컴플레인 등 민감하고 위험도가 높은(High Risk) 문의는 AI가 1차 초안만 작성한 뒤 실행을 일시 중단합니다. 이후 인간 관리자가 초안을 검토, 수정, 승인해야만 다음 단계로 넘어가는 안전망(Guardrail)을 갖추고 있습니다. 이를 통해 AI의 할루시네이션(환각)으로 인한 고객 서비스 대형 사고를 미연에 방지합니다.

## 2. 시스템 아키텍처



본 시스템은 LangGraph의 상태 관리(State Persistence)와 실행 중단(`interrupt_before`) 기능을 핵심으로 사용합니다.

1. **Classifier Node:** 고객의 문의 내용을 분석하여 카테고리와 위험도(HIGH/LOW)를 분류합니다.
2. **Drafter Node:** 문의 내용, 분류 결과, 그리고 관리자의 피드백(존재할 경우)을 종합하여 답변 초안을 작성합니다.
3. **Conditional Routing:** 위험도가 LOW일 경우 바로 Execute 단계로 넘어가고, HIGH일 경우 Human Review 단계로 라우팅합니다.
4. **Human Review (Interrupt):** 그래프 실행을 중단(Suspend)하고 대기합니다. 관리자는 UI 대시보드에서 상태를 확인하고 승인(Approve) 또는 반려(Reject) 및 피드백을 입력합니다.
5. **Feedback Loop:** 반려될 경우, 그래프는 피드백을 지닌 채 다시 Drafter Node로 돌아가 초안을 재작성합니다.
6. **Execute Node:** 최종 승인된 안전한 초안만을 처리합니다.

## 3. 기술 스택

* **Language:** Python 3.10+
* **Package Manager:** uv
* **LLM:** OpenAI gpt-4o-mini
* **Orchestration:** LangGraph, LangChain (최신 `langchain_core` 규격)
* **Web Framework:** Streamlit
* **State Management:** LangGraph `MemorySaver` (Checkpointer)

## 4. 프로젝트 구조

```text
hitl-agent/
├── .env                  # OpenAI API 키 설정
├── requirements.txt      # 의존성 패키지 목록
├── main.py               # 스트림릿 기반 UI 대시보드 (프로세스 중단 및 재개 처리)
└── app/
    ├── __init__.py
    └── graph.py          # 상태 정의, 노드 구현, LangGraph 컴파일 (interrupt_before 적용)
```

## 5. 설치 및 실행 가이드
본 프로젝트는 의존성 관리를 위해 uv를 사용합니다.

### 5.1. 사전 준비
저장소를 복제하고 프로젝트 디렉토리로 이동합니다.

```Bash
git clone [레포지토리 주소]
cd hitl-agent
```
### 5.2. 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 OpenAI API 키를 입력하십시오.

```Ini, TOML
OPENAI_API_KEY=sk-your-api-key-here
```
### 5.3. 가상환경 생성 및 패키지 설치
독립된 가상환경을 구성하고 패키지를 설치합니다.

```Bash
uv venv
uv pip install -r requirements.txt
```
### 5.4. 시스템 실행
Streamlit 애플리케이션을 구동합니다.

```Bash
uv run streamlit run main.py
```
## 6. 테스트 시나리오
애플리케이션 구동 후 아래 시나리오를 통해 상태 기반 워크플로우를 검증할 수 있습니다.

* **시나리오 A (정상 통과)**: "제품 매뉴얼은 어디서 다운로드합니까?" 입력. AI가 위험도를 LOW로 판단하여 관리자 개입 없이 프로세스를 종료합니다.

* **시나리오 B (에스컬레이션 및 승인)**: "어제 결제했는데 라이선스 키가 오지 않습니다. 당장 환불 처리해 주십시오." 입력. 위험도가 HIGH로 판정되어 프로세스가 중단됩니다. 화면에 뜬 초안을 확인 후 '승인' 버튼을 누르면 프로세스가 재개 및 종료됩니다.

* **시나리오 C (피드백 루프)**: 시나리오 B와 동일하게 중단된 상태에서, 반려 텍스트 박스에 "환불 규정 링크를 포함하여 더 정중하게 다시 작성하십시오."라고 입력한 뒤 반려 버튼을 누릅니다. 에이전트가 지시사항을 반영하여 초안을 수정한 뒤 다시 관리자 검토를 요청하는 것을 확인할 수 있습니다.

## 7. 실행 화면
<img width="1310" height="853" alt="스크린샷 2026-03-09 141141" src="https://github.com/user-attachments/assets/18b5782c-5b52-4735-ba0e-29558c68ebe1" />

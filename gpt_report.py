import streamlit as st
import json
import os
import pyperclip
import webbrowser
import pandas as pd

PROMPT_FILE = "prompts.json"

# --- 기본 템플릿 카테고리별 ---
def get_default_prompts():
    return {
        "이슈 요약": {
            "이슈 유형 정리": "아래 이슈들을 유형(예: 가격, 배송, 품질 등)별로 정리해줘. 각 유형에 해당하는 항목들을 그룹화하고 요약해줘.",
            "단순 리스트로 정리": "아래 이슈들을 항목별 리스트 형태로 간단히 요약해줘. 한 줄 요약 중심."
        },
        "인사이트 도출": {
            "3가지 인사이트": "아래 이슈들을 기반으로 3가지 주요 인사이트를 도출해줘. 각 인사이트는 제목 + 설명 + 개선 제안 포함.",
            "행동 제안 중심": "아래 이슈들을 바탕으로 우리가 실행할 수 있는 행동 아이템만 정리해줘. 항목별로 간결하게."
        },
        "리포트 문장화": {
            "보고서용 문장": "이슈 내용을 내부 보고서에 넣을 수 있도록 자연스러운 문장 형태로 정리해줘. 말투는 객관적이고, 항목마다 한 단락으로 구성.",
            "간결한 문장화": "각 이슈를 한 문장으로 요약해줘. 최대 20단어 이내로 간결하게."
        },
        "이슈 메일": {
            "이슈 전달용 메일": "이슈들을 메일 형식(제목 + 본문)으로 정리해줘. 본문은 간결하고 핵심 중심으로 작성.",
            "요약만 포함된 메일": "이슈 핵심만 요약한 짧은 메일 형식으로 정리해줘. 제목 1줄 + 본문 2~3줄."
        }
    }

# --- 포맷 구성 함수 ---
def get_formatted_prompt(title, prompt_body, issue_text):
    lines = [f"  • {line.strip()}" for line in issue_text.strip().splitlines() if line.strip()]
    formatted_issues = "\n".join(lines)
    return (
        f"[요청 유형]: {title}\n\n"
        f"[프롬프트 설명]: {prompt_body}\n\n"
        f"[입력 이슈]:\n{formatted_issues}"
    )

# --- 프롬프트 저장 로딩 ---
def load_prompts():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("prompts", {}), set(data.get("favorites", [])), data.get("recent", [])
    return {}, set(), []

# --- 프롬프트 저장 ---
def save_prompts(custom_prompts, favorites, recent):
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump({"prompts": custom_prompts, "favorites": list(favorites), "recent": recent}, f, indent=2, ensure_ascii=False)

# --- 앱 초기화 ---
def init():
    if "custom_prompts" not in st.session_state:
        st.session_state.custom_prompts, st.session_state.favorites, st.session_state.recent = load_prompts()
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "이슈 요약"
    if "selected_title" not in st.session_state:
        st.session_state.selected_title = "이슈 유형 정리"
    if "prompt_body" not in st.session_state:
        st.session_state.prompt_body = get_default_prompts()[st.session_state.selected_category][st.session_state.selected_title]

# --- 즐겨찾기 표시 ---
def decorate_title(name):
    return f"⭐ {name}" if name in st.session_state.favorites else name

def undecorate_title(name):
    return name.replace("⭐ ", "")

# --- 앱 실행 ---
def main():
    st.set_page_config(page_title="LiteGPT 프롬프트 도우미", layout="centered")
    st.title("💬 LiteGPT 프롬프트 웹 도구")
    init()

    default_prompts = get_default_prompts()
    all_prompts = default_prompts.copy()
    for cat, prompts in st.session_state.custom_prompts.items():
        if cat not in all_prompts:
            all_prompts[cat] = {}
        all_prompts[cat].update(prompts)

    st.subheader("1. 템플릿 카테고리 선택")
    tab_labels = list(all_prompts.keys())
    active_tab = st.radio("", tab_labels, horizontal=True)

    cat_name = active_tab
    st.session_state.selected_category = cat_name

    all_titles = list(all_prompts[cat_name].keys())
    sorted_titles = sorted(all_titles, key=lambda x: (x not in st.session_state.favorites, x))
    decorated_options = [decorate_title(t) for t in sorted_titles]

    selection = st.selectbox("세부 템플릿 선택", decorated_options, key=f"select_{cat_name}")
    selected_title = undecorate_title(selection)
    if st.session_state.selected_title != selected_title:
        st.session_state.selected_title = selected_title
        st.session_state.prompt_body = all_prompts[cat_name][selected_title]

    if st.button("⭐ 즐겨찾기 등록/해제", key=f"fav_{cat_name}"):
        if selected_title in st.session_state.favorites:
            st.session_state.favorites.remove(selected_title)
        else:
            st.session_state.favorites.add(selected_title)
        save_prompts(st.session_state.custom_prompts, st.session_state.favorites, st.session_state.recent)
        st.experimental_rerun()

    with st.expander("➕ 프롬프트 추가하기"):
        new_title = st.text_input("프롬프트 제목", key=f"add_title_{cat_name}")
        new_content = st.text_area("프롬프트 내용", key=f"add_content_{cat_name}")
        if st.button("저장", key=f"save_{cat_name}"):
            if new_title and new_content:
                if cat_name not in st.session_state.custom_prompts:
                    st.session_state.custom_prompts[cat_name] = {}
                st.session_state.custom_prompts[cat_name][new_title] = new_content
                save_prompts(st.session_state.custom_prompts, st.session_state.favorites, st.session_state.recent)
                st.success("프롬프트가 추가되었습니다. 새로고침하면 반영됩니다.")

    with st.expander("🗑 프롬프트 삭제하기"):
        if cat_name in st.session_state.custom_prompts:
            deletables = list(st.session_state.custom_prompts[cat_name].keys())
            del_selection = st.multiselect("삭제할 프롬프트 선택", deletables, key=f"delete_{cat_name}")
            if st.button("삭제", key=f"delete_btn_{cat_name}"):
                for d in del_selection:
                    st.session_state.custom_prompts[cat_name].pop(d, None)
                save_prompts(st.session_state.custom_prompts, st.session_state.favorites, st.session_state.recent)
                st.success("삭제 완료! 새로고침 시 반영됩니다.")

    st.divider()

    if st.session_state.recent:
        with st.expander("🕓 최근 사용한 프롬프트"):
            for r in st.session_state.recent[-5:][::-1]:
                st.markdown(f"- **{r}**")

    st.subheader("2. 이슈 입력")
    issue_text = st.text_area("🧾 키워드 이슈를 입력하세요", height=180, placeholder="각 줄마다 다른 이슈를 입력해 주세요." )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📋 복사 & ChatGPT 열기"):
            formatted = get_formatted_prompt(
                st.session_state.selected_title, 
                st.session_state.prompt_body, issue_text)
            pyperclip.copy(formatted)
            webbrowser.open("https://chat.openai.com")
            if st.session_state.selected_title not in st.session_state.recent:
                st.session_state.recent.append(st.session_state.selected_title)
            save_prompts(st.session_state.custom_prompts, st.session_state.favorites, st.session_state.recent)
            st.success("✅ 복사 완료! ChatGPT에 붙여넣기만 하면 돼요.")
    with col2:
        if st.button("👀 미리보기"):
            st.text_area("📎 붙여넣을 프롬프트 내용", get_formatted_prompt(st.session_state.selected_title, st.session_state.prompt_body, issue_text), height=300)

if __name__ == "__main__":
    main()

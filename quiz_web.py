import streamlit as st
import csv
import random
from pathlib import Path

DATA_FILE_DEFAULT = "quiz.csv"
ERROR_FILE = "errori.csv"

# Funzioni di utilità
def normalize_row(row):
    return [(cell or "").strip().lstrip("\ufeff") for cell in row[:6]]

def load_questions(path: Path):
    questions = []
    if not path.exists():
        return questions
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        for i, row in enumerate(reader):
            if not row:
                continue
            row = normalize_row(row)
            if len(row) < 6:
                continue
            domanda, A, B, C, D, corr = row
            if i == 0 and corr.upper() not in ("A", "B", "C", "D"):
                continue
            corr = corr.upper()
            if corr not in ("A", "B", "C", "D"):
                continue
            questions.append({
                "domanda": domanda,
                "A": A, "B": B, "C": C, "D": D,
                "corretta": corr
            })
    return questions

def save_errors(questions, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        for q in questions:
            writer.writerow([q["domanda"], q["A"], q["B"], q["C"], q["D"], q["corretta"]])

# Stato iniziale
if "mode_selected" not in st.session_state:
    st.session_state.mode_selected = False
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "num_questions" not in st.session_state:
    st.session_state.num_questions = 0

st.set_page_config(page_title="Quiz Web", page_icon="📝", layout="centered")
st.title("📝 Quiz Web con Streamlit")
st.markdown("Allenati con le tue domande, anche da tablet 📱")

# Selezione modalità
if not st.session_state.mode_selected:
    st.header("⚙️ Impostazioni iniziali")
    mode = st.radio("Seleziona la modalità:", ["Tutte le domande", "Solo errori"])
    data_path = Path(DATA_FILE_DEFAULT)
    error_path = Path(ERROR_FILE)

    if mode == "Tutte le domande":
        chosen_path = data_path
    else:
        if error_path.exists():
            chosen_path = error_path
        else:
            st.warning("⚠️ Nessun file errori.csv trovato, uso quiz.csv")
            chosen_path = data_path

    questions = load_questions(chosen_path)
    if not questions:
        st.error("❌ Nessuna domanda trovata nel file selezionato.")
        st.stop()

    st.subheader("📋 Anteprima prime 5 domande")
    for q in questions[:5]:
        st.write(f"**{q['domanda']}**")
        st.write(f"A) {q['A']}")
        st.write(f"B) {q['B']}")
        st.write(f"C) {q['C']}")
        st.write(f"D) {q['D']}")
        st.write("---")

    num = st.number_input("Quante domande vuoi fare?", min_value=1, max_value=len(questions), value=min(10, len(questions)), step=1)

    if st.button("🎯 Inizia il quiz"):
        st.session_state.mode_selected = True
        st.session_state.quiz_started = True
        st.session_state.questions = random.sample(questions, k=num)
        st.session_state.num_questions = num
        st.session_state.current_index = 0
        st.session_state.answers = [None] * num
        st.experimental_rerun()

# Esecuzione quiz
elif st.session_state.quiz_started and st.session_state.current_index < st.session_state.num_questions:
    idx = st.session_state.current_index
    q = st.session_state.questions[idx]

    st.progress((idx) / st.session_state.num_questions)
    st.subheader(f"Domanda {idx+1}/{st.session_state.num_questions}")
    st.markdown(f"**{q['domanda']}**")
    choice = st.radio("Seleziona la tua risposta:", ["A", "B", "C", "D"], format_func=lambda x: f"{x}) {q[x]}", index=None if st.session_state.answers[idx] is None else ["A","B","C","D"].index(st.session_state.answers[idx]))

    if st.button("Conferma risposta"):
        if choice is None:
            st.warning("❗ Devi selezionare una risposta prima di confermare.")
        else:
            st.session_state.answers[idx] = choice
            st.session_state.current_index += 1
            st.experimental_rerun()

# Risultati finali
elif st.session_state.quiz_started:
    st.subheader("📊 Risultati")
    total = st.session_state.num_questions
    score = sum(1 for i, q in enumerate(st.session_state.questions) if st.session_state.answers[i] == q["corretta"])
    perc = score / total * 100
    st.success(f"Hai ottenuto {score}/{total} • {perc:.1f}%")

    wrong = []
    for i, q in enumerate(st.session_state.questions):
        if st.session_state.answers[i] != q["corretta"]:
            wrong.append((q, st.session_state.answers[i]))

    if wrong:
        st.error(f"Hai sbagliato {len(wrong)} domande:")
        for i, (q, ans) in enumerate(wrong, 1):
            st.markdown(f"**{i}) {q['domanda']}**")
            st.markdown(f"❌ Tua risposta: {ans}) {q[ans] if ans else ''}")
            corr = q['corretta']
            st.markdown(f"✅ Corretta: {corr}) {q[corr]}")
            st.write("---")

        # Salva errori
        wrong_questions = [q for q, _ in wrong]
        save_errors(wrong_questions, Path(ERROR_FILE))
        st.info("Gli errori sono stati aggiunti a errori.csv")
    else:
        st.balloons()
        st.success("Perfetto! Nessun errore 🎉")

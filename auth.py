import os
import streamlit as st


def _get_credentials():
    user = os.environ.get("APP_USERNAME", "")
    pwd = os.environ.get("APP_PASSWORD", "")
    return user, pwd


def is_configured():
    user, pwd = _get_credentials()
    return bool(user) and bool(pwd)


def is_authenticated():
    return st.session_state.get("authenticated", False)


def login_form():
    user, pwd = _get_credentials()

    if not user or not pwd:
        st.error("Autenticazione non configurata. Imposta le variabili d'ambiente APP_USERNAME e APP_PASSWORD.")
        return

    with st.form("login_form"):
        st.markdown("### 🔒 Accedi ad AppFoto")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        submitted = st.form_submit_button("Entra")

    if submitted:
        if username == user and password == pwd:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Credenziali errate.")


def require_login():
    if is_authenticated():
        return
    login_form()
    st.stop()

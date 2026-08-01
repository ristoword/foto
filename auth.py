import os
import streamlit as st
import db


def _get_env_credentials():
    user = os.environ.get("APP_USERNAME", "")
    pwd = os.environ.get("APP_PASSWORD", "")
    return user, pwd


def _use_db():
    return bool(os.environ.get("DATABASE_URL", "")) and db.PSYCOPG2_AVAILABLE


def is_authenticated():
    return st.session_state.get("authenticated", False)


def _login_with_env(username, password):
    user, pwd = _get_env_credentials()
    return username == user and password == pwd


def _login_with_db(username, password):
    return db.authenticate(username, password)


def _create_first_user(username, password):
    if _use_db() and not db.user_exists(username):
        return db.create_user(username, password)
    return False


def login_form():
    db_ok = _use_db()

    if db_ok:
        db.init_db()

    if db_ok and not db.has_users() and not _get_env_credentials()[0]:
        st.markdown("### 🔒 Crea il primo account admin")
        with st.form("create_first_user"):
            new_user = st.text_input("Username admin", key="first_user")
            new_pwd = st.text_input("Password admin", type="password", key="first_pwd")
            submit = st.form_submit_button("Crea")
        if submit:
            if not new_user or not new_pwd:
                st.error("Inserisci username e password.")
            else:
                if _create_first_user(new_user, new_pwd):
                    st.session_state.authenticated = True
                    st.session_state.username = new_user
                    st.rerun()
                else:
                    st.error("Errore nella creazione dell'utente.")
        st.stop()
        return

    with st.form("login_form"):
        st.markdown("### 🔒 Accedi ad AppFoto")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        submitted = st.form_submit_button("Entra")

    if submitted:
        ok = False
        if db_ok:
            user_id = _login_with_db(username, password)
            ok = user_id is not None
            st.session_state.user_id = user_id
        else:
            ok = _login_with_env(username, password)

        if ok:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Credenziali errate.")


def require_login():
    if is_authenticated():
        return
    login_form()
    st.stop()


def current_user_id():
    return st.session_state.get("user_id")

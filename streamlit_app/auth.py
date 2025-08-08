# Lógica de login y roles
import streamlit as st
from config import USERS


def login_section():
    """Muestra el formulario de login y maneja la autenticación"""
    st.title("🔑 Inicio de Sesión")

    username = st.text_input("Usuario", key="auth_username")
    password = st.text_input("Contraseña", type="password", key="auth_password")

    if st.button("Ingresar", key="auth_ingresar"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = USERS[username]["role"]
            st.experimental_rerun()
        else:
            st.error("Credenciales incorrectas")


def require_login():
    if "logged_in" not in st.session_state:
        login_section()
        st.stop()


def logout_button(key="logout_button"):
    if st.button("🔒 Cerrar sesión", key=key):
        st.session_state.clear()
        st.experimental_rerun()
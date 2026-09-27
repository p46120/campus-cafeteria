import streamlit as st

st.set_page_config(
    page_title="Campus Cafeteria",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Campus Cafeteria")
st.subheader("Pre-Order & Queue Management System")

st.info(
    "Welcome! This platform will allow students to pre-order food "
    "and help the cafeteria manage orders efficiently."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👨‍🎓 Student Portal")
    st.write("View today's menu, place orders and track your order.")
    
    if st.button("Open Student Portal", use_container_width=True):
        st.success("Student Portal will be built here.")

with col2:
    st.markdown("### 👨‍🍳 Cafeteria Portal")
    st.write("Manage menu, view orders and update order status.")
    
    if st.button("Open Cafeteria Portal", use_container_width=True):
        st.success("Cafeteria Portal will be built here.")

st.divider()

st.caption("Campus Cafeteria Management System — Prototype")

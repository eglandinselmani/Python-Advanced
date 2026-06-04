import streamlit as st

tab1,tab2,tb3 = st.tabs(["Tab 1","Tab 2","Tab 3"])


with tab1:
    st.header("Conent for Tab 1")
    st.write("this is the content of the first tab")

with tab2:
    st.header("Conent for Tab 2")
    st.write("this is the content of the first tab")

with tab3:
    st.header("Conent for Tab 3")
    st.write("this is the content of the first tab")



















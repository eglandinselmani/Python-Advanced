import streamlit as st

st.title("BMI Calculator")

weight = st.number_input("Enter your weight (kg)", min_value=1.0)
height = st.number_input("Enter your height (m)", min_value=0.1)

if st.button("Calculate BMI"):
    bmi = weight / (height ** 2)

    st.write(f"Your BMI is: {bmi:.2f}")

    if bmi < 18.5:
        st.success("Underweight")
    elif bmi < 25:
        st.success("Normal weight")
    elif bmi < 30:
        st.warning("Overweight")
    else:
        st.error("Obese")
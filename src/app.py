import streamlit as st
import pandas as pd
 
st.set_page_config(page_title="My Streamlit App", layout="wide")
 
st.title("Streamlit in VS Code")
st.write("This app demonstrates core Streamlit widgets running inside VS Code.")
 
# Sidebar controls
st.sidebar.header("Configuration")
name = st.sidebar.text_input("Your name", value="Developer")
num_rows = st.sidebar.slider("Number of rows", min_value=5, max_value=100, value=20)
 
# Generate sample data
data = pd.DataFrame({
    "Category": [f"Item {i}" for i in range(num_rows)],
    "Value": [i * 3.14 for i in range(num_rows)],
    "Status": ["Active" if i % 2 == 0 else "Inactive" for i in range(num_rows)]
})
 
st.subheader(f"Hello, {name}! Here is your data:")
 
# Display metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Items", len(data))
col2.metric("Active", len(data[data["Status"] == "Active"]))
col3.metric("Average Value", f"{data['Value'].mean():.2f}")
 
# Display the dataframe
st.dataframe(data, use_container_width=True)
 
# Simple chart
st.line_chart(data.set_index("Category")["Value"])

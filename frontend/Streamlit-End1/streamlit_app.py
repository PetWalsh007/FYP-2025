import streamlit as st
import requests
###

# References:
    # https://docs.streamlit.io/get-started/fundamentals/main-concepts
    # https://docs.streamlit.io/develop/concepts/custom-components/create
   # https://docs.streamlit.io/develop/concepts/configuration




st.title("Query Builder App") 



selected_param = st.selectbox("Select Tags", list(range(1, 11)))

cols = st.columns(selected_param)
parameters = []
for i, col in enumerate(cols):
    with col:
        param = st.text_input(f"Tag Name {i+1}", f"param_{i+1}")
        parameters.extend(param.split(","))

# User defines aggregations dynamically
aggregation_options = ["sum", "average", "min", "max", "count", "ROC", "stddev", "Cumulative Sum"]
aggregations = {}

for i, param in enumerate(parameters):
    col = cols[i % selected_param]
    with col:
        agg = st.selectbox(f"Operation on {param}", aggregation_options, index=1)  # Default to "average"
        aggregations[param] = agg



if parameters:
    group_by = st.selectbox("Group By", parameters)
else:
    group_by = None

# Json payload
query_payload = {
    "tagname": parameters,
    "aggregations": aggregations,
    "group_by": group_by
}

# Display the JSON
st.json(query_payload)


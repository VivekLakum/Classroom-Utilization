import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
# ----------------------------
# Load Data
# ----------------------------
df = pd.read_csv("C:\Users\Vivek\Downloads\my_project\data\all_rooms_timetable.csv")

# Make sure types are right
df["room_name"] = df["room_name"].astype(str)

# Extract block like BL1, BL2, ...
df["block"] = df["room_name"].str.extract(r"(BL\d+)")

# IMPORTANT FIX:
# One real usage event = one room + one day + one time
events = df.drop_duplicates(subset=["room_name", "day", "time"])

# Now compute usage from EVENTS, not raw df
room_usage = events.groupby(["block", "room_name"]).size().reset_index(name="usage_count")
time_usage = events.groupby("time").size().reset_index(name="usage_count")

# ----------------------------
# App State
# ----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_block" not in st.session_state:
    st.session_state.selected_block = None

if "operation" not in st.session_state:
    st.session_state.operation = None

# ----------------------------
# Page 1: Home (Select Block)
# ----------------------------
if st.session_state.page == "home":
    st.title("🏫 Classroom Utilization Analytics")

    blocks = sorted(room_usage["block"].dropna().unique())
    block = st.selectbox("Select Block", blocks)

    if st.button("Continue"):
        st.session_state.selected_block = block
        st.session_state.page = "operations"

# ----------------------------
# Page 2: Select Operation
# ----------------------------
elif st.session_state.page == "operations":
    st.title(f"🔎 Block {st.session_state.selected_block}")

    st.write("Select what you want to see:")

    if st.button("📈 Most Utilized Rooms"):
        st.session_state.operation = "most"
        st.session_state.page = "visual"

    if st.button("📉 Least Utilized Rooms"):
        st.session_state.operation = "least"
        st.session_state.page = "visual"

    if st.button("⏰ Time-wise Usage"):
        st.session_state.operation = "time"
        st.session_state.page = "visual"

    if st.button("📊 Full Overview"):
        st.session_state.operation = "overview"
        st.session_state.page = "visual"

    if st.button("⬅️ Back"):
        st.session_state.page = "home"

# ----------------------------
# Page 3: Visualization
# ----------------------------
elif st.session_state.page == "visual":
    block = st.session_state.selected_block
    op = st.session_state.operation

    st.title(f"📊 Results for Block {block}")

    # 1. Prepare base data
    block_data = room_usage[room_usage["block"] == block].sort_values("usage_count", ascending=False)

    # 2. MOVE FILTERS HERE (So 'filtered' is defined before use)
    st.subheader("Filters")
    search_text = st.text_input("Search room (e.g., 3014):", "")
    
    # Safely get max usage for the slider
    max_val = int(block_data["usage_count"].max()) if not block_data.empty else 100
    min_usage = st.slider("Minimum usage to show", 0, max_val, 0)

    # Apply filters to create the 'filtered' dataframe
    filtered = block_data.copy()
    if search_text:
        filtered = filtered[filtered["room_name"].str.contains(search_text, case=False, na=False)]
    
    filtered = filtered[filtered["usage_count"] >= min_usage]

    # 3. Now handle the operations using the 'filtered' data
    if op == "most":
        st.subheader("Most Utilized Rooms (Interactive)")
        data = filtered.sort_values("usage_count", ascending=False).head(20)

        if not data.empty:
            chart = (
                 alt.Chart(data)
                .mark_bar()
                .encode(
                    x=alt.X("room_name:N", sort=None, title="Room"),
                    y=alt.Y("usage_count:Q", title="Usage Count"),
                    tooltip=["room_name", "usage_count"],
                )
                .properties(height=400)
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)
            
            best = data.iloc[0]
            st.success(f"Most used room: {best['room_name']} ({best['usage_count']} time slots)")
        else:
            st.info("No rooms match your filters.")

    elif op == "least":
        st.subheader("Least Utilized Rooms (Interactive)")
        data = filtered.sort_values("usage_count", ascending=True).head(20)

        if not data.empty:
            chart = (
                alt.Chart(data)
                .mark_bar()
                .encode(
                    x=alt.X("room_name:N", sort=None, title="Room"),
                    y=alt.Y("usage_count:Q", title="Usage Count"),
                    tooltip=["room_name", "usage_count"],
                )
                .properties(height=400)
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)
            
            worst = data.iloc[0]
            st.warning(f"Least used room: {worst['room_name']} ({worst['usage_count']} time slots)")
        else:
            st.info("No rooms match your filters.")

    elif op == "time":
        st.subheader("Time-wise Usage (All Blocks)")
        st.line_chart(time_usage.set_index("time")["usage_count"])

        peak = time_usage.loc[time_usage["usage_count"].idxmax()]
        dead = time_usage.loc[time_usage["usage_count"].idxmin()]

        st.success(f"Peak time: {peak['time']} ({peak['usage_count']} classes)")
        st.warning(f"Least used time: {dead['time']} ({dead['usage_count']} classes)")

    elif op == "overview":
        st.subheader("Overview: Room Usage in This Block")
        # Use filtered data here too for consistency
        st.bar_chart(filtered.set_index("room_name")["usage_count"])

    # 4. Back button at the very bottom
    if st.button("⬅️ Back to Operations"):
        st.session_state.page = "operations"

        st.rerun() # Use rerun to refresh the page state immediately

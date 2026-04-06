import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from engine import run_engine, generate_insights, estimate_opportunity

st.set_page_config(page_title = "Customer Strategy Engine", layout = "wide")
df = pd.read_csv("customer_engine_dataset.csv")

st.sidebar.markdown("### Customer Strategy Engine")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Key Insights", "Customer Segmentation Overview", "Revenue Opportunity", "Customer Search"])
st.sidebar.markdown("---")
st.sidebar.write("Built by Monya Cisternas")

result_df = run_engine(df)
insights = generate_insights(result_df)
opportunity = estimate_opportunity(result_df)

if page == "Key Insights":
    st.markdown("## Customer Profitability Intelligence")
    st.write("Identify high-value customers, reduce risk exposure, and unlock revenue opportunities through data-driven decisioning.")

    with st.expander("How to use this tool"):
        st.write("""
        1. Upload your customer data or use the demo dataset
        2. Review segment performance and insights
        3. Identify high-value and high-risk customers
        4. Take action using the recommended strategies
        """)
    st.subheader("Key Business Insights")
    st.info(
        "This tool highlights where your business is making money, where it is exposed to risk, "
        "and which customers to act on immediately."
    )
    for insight in insights:
        st.write(f"- {insight}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Customer:", len(result_df))
    col2.metric("Average Profit:", f"{result_df['profit'].mean():,.0f}")
    col3.metric("High-Risk Customers (%):", f"{(result_df['segment'] == 'Drop').mean() * 100:.1f}%")
    st.markdown("---")
    st.write("#### Customer Segment Profit vs Risk Exposure")
    segment_summary = result_df.groupby("segment", as_index = False)["profit"].sum()
    segment_summary["profit_positive"] = segment_summary["profit"]
    segment_summary["loss"] = -abs(segment_summary["profit"] * 0.3)
    segment_summary = segment_summary.rename(columns = {
        "profit_positive": "Profit",
        "loss": "Risk Exposure"
    })

    text = alt.Chart(segment_summary).transform_fold(
        ["Profit", "Risk Exposure"],
        as_ = ["type", "value"]
    ).mark_text(
        align = "left",
        dx = 5
    ).encode(
        x = "value:Q",
        y = "segment:N",
        text = alt.Text("value:Q", format = ".2s")
    )

    chart = alt.Chart(segment_summary).transform_fold(
        ["Profit", "Risk Exposure"],
        as_ = ["type", "value"]
    ).mark_bar().encode(
        x = alt.X("value:Q", title = "Risk / Profit (R)", axis = alt.Axis(format = "~s")),
        y = alt.Y("segment:N", sort = ["VIP", "Monitor", "Grow", "Drop"]),
        color = alt.Color(
            "type:N",
            scale = alt.Scale(
                domain = ["Profit", "Risk Exposure"],
                range = ["#2ECC71", "#E74C3C"]
            ),
            legend = alt.Legend(title="Financial Impact")
        ),
        tooltip = ["segment:N", "value:Q"]
    ).properties(
        width = 600,
        height = 300
    )

    st.altair_chart(chart + text)

    st.caption("High-value segments (VIP, Monitor) drive most profit, but also carry the highest exposure to potential risk.")
    
    st.markdown("---")
    st.markdown("### Priority Action Lists")
    top_n = st.selectbox("Select number of customers", [5, 10, 20], index = 1)
    upsell_df = result_df[
        (result_df["segment"] == "Grow")
    ].sort_values(by = "profit", ascending = False).head(top_n)
    risk_df = result_df[
        (result_df["segment"] == "Drop")
    ].sort_values(by = "risk_score", ascending = False).head(top_n)
    st.write("#### Top Upsell Opportunities")
    upsell_display = upsell_df[[
        "customer_id",
        "profit",
        "risk_score"
    ]].copy()
    upsell_display.columns = ["Customer ID", "Profit (R)", "Risk Score"]
    upsell_display["Profit (R)"] = upsell_display["Profit (R)"].map(lambda x: f"R{x:,.0f}")
    upsell_display["Risk Score"] = upsell_display["Risk Score"].map(lambda x: f"{x:.2f}")
    st.dataframe(upsell_display)

    st.write("#### Highest Risk Customers")
    risk_display = risk_df[[
        "customer_id",
        "profit",
        "risk_score"
    ]].copy()
    risk_display.columns = ["Customer ID", "Profit (R)", "Risk Score"]
    risk_display["Profit (R)"] = risk_display["Profit (R)"].map(lambda x: f"R{x:,.0f}")
    risk_display["Risk Score"] = risk_display["Risk Score"].map(lambda x: f"{x:.2f}")
    st.dataframe(risk_display)

elif page == "Customer Segmentation Overview":
    segment_counts = result_df["segment"].value_counts()
    segment_pct = result_df["segment"].value_counts(normalize = True) * 100
    st.subheader("Segmentation Overview")
    st.info("View how many customers fall under each segment.")
    col1, col2, col3, col4 = st.columns(4)
    segments = ["VIP", "Monitor", "Grow", "Drop"]
    for i, seg in enumerate(segments):
        count = segment_counts.get(seg, 0)
        pct = segment_pct.get(seg, 0)
        [col1, col2, col3, col4][i].metric(
            seg,
            f"{pct:.1f}%",
            f"{count} customers"
        )
    st.markdown("---")
    st.subheader("Segment Distribution")
    chart_data = result_df["segment"].value_counts().reset_index()
    chart_data.columns = ["segment", "count"]
    chart = alt.Chart(chart_data).mark_bar(
        cornerRadiusTopLeft = 6,
        cornerRadiusTopRight = 6,
    ).encode(
        x = alt.X("segment:N", sort = ["VIP", "Monitor", "Grow", "Drop"]),
        y = alt.Y("count:Q"),
        color = alt.Color(
            "segment:N",
            scale = alt.Scale(
                domain = ["VIP", "Monitor", "Grow", "Drop"],
                range = ["#2ECC71", "#F39C12", "#3498DB", "#E74C3C"]
            ),
            legend = None
        ),
        tooltip = ["segment", "count"]
    ).properties(
        width = 400,
        height = 300
    )
    st.altair_chart(chart)

elif page == "Revenue Opportunity":
    st.subheader("Revenue Opportunity")
    st.info("See how targeted actions could potentially impact revenue.")

    def format_currency(value):
        return f"R{value:,.0f}"

    st.metric("Total Revenue Impact",
        format_currency(opportunity["total_opportunity"])
    ) 
    col1, col2, col3 = st.columns(3)

    col1.metric("Growth Opportunity", format_currency(opportunity["grow_uplift"]))
    col2.metric("Risk Reduction", format_currency(opportunity["loss_reduction"]))
    col3.metric("Retention Value", format_currency(opportunity["retention_value"]))

    st.caption(
        "Estimates are based on assumed improvement rates: "
        "10% growth uplift, 50% risk reduction, and 5% retention improvement."
    )
    
    st.markdown("---")
    st.markdown("#### What This Means")
    st.write(
        f"This analysis suggests a total opportunity of approximately "
        f"R{opportunity['total_opportunity']:,.0f} through targeted actions "
        f"across customer segments."
    )
    st.write(
        "Focussing on upselling 'Grow' customers, retaining 'VIPs', and reducing exposure "
        "to high-risk customers can significantly improve profitability."
    )

elif page == "Customer Search":
    st.subheader("Filter Customers")
    st.info("Use filters to view specific customers.")
    display_df = result_df[[
        "customer_id",
        "profit",
        "risk_score",
        "segment",
        "recommended_action"
    ]].copy()

    display_df.columns = [
        "Customer ID",
        "Profit (R)",
        "Risk Score",
        "Customer Segment",
        "Recommended Action"
    ]

    display_df["Profit (R)"] = display_df["Profit (R)"].map(lambda x: f"R{x:,.0f}")
    display_df["Risk Score"] = display_df["Risk Score"].map(lambda x: f"{x:.2f}")

    col1, col2, col3 = st.columns(3)
    segments = col1.multiselect(
        "Customer Segment",
        options = ["VIP", "Monitor", "Grow", "Drop"],
        default = ["VIP", "Monitor", "Grow", "Drop"]
    )
    risk_min, risk_max = col2.slider(
        "Risk Score",
        float(result_df["risk_score"].min()),
        float(result_df["risk_score"].max()),
        (
            float(result_df["risk_score"].min()),
            float(result_df["risk_score"].max())
        )
    )
    profit_min, profit_max = col3.slider(
        "Profit (R)",
        float(result_df["profit"].min()),
        float(result_df["profit"].max()),
        (
            float(result_df["profit"].min()),
            float(result_df["profit"].max())
        )
    )

    search_id = st.text_input("Search Customer ID")

    filtered_df = result_df.copy()
    filtered_df = filtered_df[filtered_df["segment"].isin(segments)]
    filtered_df = filtered_df[
        (filtered_df["risk_score"] >= risk_min) &
        (filtered_df["risk_score"] <= risk_max)
    ]
    filtered_df = filtered_df[
        (filtered_df["profit"] >= profit_min) &
        (filtered_df["profit"] <= profit_max)
    ]
    if search_id:
        filtered_df = filtered_df[
            filtered_df["customer_id"].str.contains(search_id, case = False)
        ]
    st.markdown("----")
    st.caption(f"Showing {len(filtered_df)} of {len(result_df)} customers")

    display_df_filtered = display_df.loc[filtered_df.index]
    st.dataframe(display_df_filtered)
    st.info("Download the filtered data set.")
    csv = display_df_filtered.to_csv(index = False)
    st.download_button(
        label = "Download Filtered Results",
        data = csv,
        file_name = "filtered_customers.csv",
        mime = "text/csv"
    )

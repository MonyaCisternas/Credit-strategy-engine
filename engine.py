import pandas as pd
import numpy as np

def normalize(col):
    return (col - col.min()) / (col.max() - col.min())

def run_engine(df):

    df = df.copy()

    # Profit
    df["profit"] = df["total_revenue"] - df["cost_to_serve"]
    df["profit_score"] = normalize(df["profit"])

    # Risk
    df["risk_score"] = (
        0.4 * normalize(df["payment_delay_days"]) +
        0.4 * normalize(df["missed_payments"]) +
        0.2 * normalize(df["last_purchase_days"])
    )

    # Thresholds
    profit_threshold = df["profit_score"].quantile(0.5)
    risk_threshold = df["risk_score"].quantile(0.5)

    # Segmentation
    def assign_segment(row):
        if row["profit_score"] >= profit_threshold and row["risk_score"] < risk_threshold:
            return "VIP"
        elif row["profit_score"] >= profit_threshold and row["risk_score"] >= risk_threshold:
            return "Monitor"
        elif row["profit_score"] < profit_threshold and row["risk_score"] < risk_threshold:
            return "Grow"
        else:
            return "Drop"

    df["segment"] = df.apply(assign_segment, axis=1)

    # Actions
    def recommend_action(segment):
        return {
            "VIP": "Reward loyalty",
            "Monitor": "Monitor / restrict credit",
            "Grow": "Upsell / marketing",
            "Drop": "Reduce exposure"
        }[segment]

    df["recommended_action"] = df["segment"].apply(recommend_action)

    return df

def generate_insights(df):
    insights = []

    total_customers = len(df)

    vip_pct = (df["segment"] == "VIP").mean() * 100
    drop_pct = (df["segment"] == "Drop").mean() * 100
    monitor_pct = (df["segment"] == "Monitor").mean() * 100

    avg_profit = df["profit"].mean()
    total_profit = df["profit"].sum()

    # Insight 1: VIP concentration
    insights.append(
        f"{vip_pct:.1f}% of customers are high-value (VIP). Focus on retention and loyalty strategies here."
    )

    # Insight 2: Risky customers
    insights.append(
        f"{drop_pct:.1f}% of customers are high-risk and unprofitable. Reducing exposure here could improve overall margins."
    )

    # Insight 3: Monitor segment
    insights.append(
        f"{monitor_pct:.1f}% of customers require close monitoring due to elevated risk."
    )

    # Insight 4: Profit overview
    insights.append(
        f"Total estimated profit across customers is R{total_profit:,.0f}, with an average of R{avg_profit:,.0f} per customer."
    )

    return insights

def estimate_opportunity(df):
    
    # Grow segment → potential revenue increase
    grow_df = df[df["segment"] == "Grow"]
    grow_revenue = grow_df["total_revenue"].sum()
    grow_uplift = grow_revenue * 0.10  # assume 10% uplift
    
    # Drop segment → potential loss reduction
    drop_df = df[df["segment"] == "Drop"]
    drop_loss = drop_df["profit"].sum()
    loss_reduction = abs(drop_loss) * 0.50  # assume 50% reduction
    
    # VIP → retention value
    vip_df = df[df["segment"] == "VIP"]
    vip_revenue = vip_df["total_revenue"].sum()
    retention_value = vip_revenue * 0.05  # 5% retention boost
    
    return {
        "grow_uplift": grow_uplift,
        "loss_reduction": loss_reduction,
        "retention_value": retention_value,
        "total_opportunity": grow_uplift + loss_reduction + retention_value
    }

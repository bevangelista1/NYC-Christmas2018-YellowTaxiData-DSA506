import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="NYC Yellow Taxi Holiday Dashboard", page_icon="🚕", layout="wide")

TAXI_ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv("taxi_christmas_2018_cleaned.csv.gz", parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"])

    # TLC taxi zone lookup table: LocationID, Borough, Zone, service_zone.
    # This is joined twice: once for pickup location and once for dropoff location.
    zones = pd.read_csv(TAXI_ZONE_LOOKUP_URL)
    zones["LocationID"] = zones["LocationID"].astype(int)

    pu_zones = zones.rename(columns={
        "LocationID": "PULocationID",
        "Borough": "PU_Borough",
        "Zone": "PU_Zone",
        "service_zone": "PU_Service_Zone"
    })
    do_zones = zones.rename(columns={
        "LocationID": "DOLocationID",
        "Borough": "DO_Borough",
        "Zone": "DO_Zone",
        "service_zone": "DO_Service_Zone"
    })

    df = df.merge(pu_zones, on="PULocationID", how="left")
    df = df.merge(do_zones, on="DOLocationID", how="left")
    df["PU_Label"] = df["PU_Borough"].fillna("Unknown") + " — " + df["PU_Zone"].fillna("Unknown")
    df["DO_Label"] = df["DO_Borough"].fillna("Unknown") + " — " + df["DO_Zone"].fillna("Unknown")
    return df

df = load_data()

st.title("🚕 NYC Yellow Taxi Trips: Christmas Eve–Christmas Day 2018")
st.markdown("""
This dashboard follows the **QUEST** exploratory data analysis structure: **Question, Understand, Explore, Study, Tell**.  
NYC Department of Transportation: How do holiday taxi demand, trip length, fare behavior, geography, and tipping patterns change across Christmas Eve and Christmas Day?
""")

st.sidebar.header("Interactive filters")
#min_dt = df["tpep_pickup_datetime"].min().to_pydatetime()
#max_dt = df["tpep_pickup_datetime"].max().to_pydatetime()
#start_dt, end_dt = st.sidebar.slider("Pickup date/time range", min_value=min_dt, max_value=max_dt, value=(min_dt, max_dt), format="MM/DD HH:mm")
payment_opts = sorted(df["payment_label"].dropna().unique())
selected_payments = st.sidebar.multiselect("Payment type", payment_opts, default=payment_opts)
pickup_borough_options = sorted(df["PU_Borough"].dropna().unique())
dropoff_borough_options = sorted(df["DO_Borough"].dropna().unique())
selected_pickup_boroughs = st.sidebar.multiselect("Pickup borough", pickup_borough_options, default=pickup_borough_options)
selected_dropoff_boroughs = st.sidebar.multiselect("Dropoff borough", dropoff_borough_options, default=dropoff_borough_options)
max_distance = float(np.nanpercentile(df["trip_distance"], 99))
distance_range = st.sidebar.slider("Trip distance range (miles)", 0.0, max(1.0, round(max_distance, 1)), (0.0, max(1.0, round(max_distance, 1))))
keep_plausible = st.sidebar.checkbox("Use plausible trip filter", value=True, help="Keeps positive trips with duration ≤ 180 min, distance ≤ 100 miles, and nonnegative total amount.")

f = df[
    (df["tpep_pickup_datetime"].between(pd.Timestamp(start_dt), pd.Timestamp(end_dt))) &
    (df["payment_label"].isin(selected_payments)) &
    (df["trip_distance"].between(distance_range[0], distance_range[1])) &
    (df["PU_Borough"].isin(selected_pickup_boroughs)) &
    (df["DO_Borough"].isin(selected_dropoff_boroughs))
].copy()
if keep_plausible:
    f = f[(f["trip_duration_min"] > 0) & (f["trip_duration_min"] <= 180) & (f["trip_distance"] > 0) & (f["trip_distance"] <= 100) & (f["total_amount"] >= 0)]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Trips", f"{len(f):,}")
k2.metric("Median distance", f"{f['trip_distance'].median():.2f} mi" if len(f) else "—")
k3.metric("Median duration", f"{f['trip_duration_min'].median():.1f} min" if len(f) else "—")
k4.metric("Median total fare", f"${f['total_amount'].median():.2f}" if len(f) else "—")
k5.metric("Median tip %", f"{f['tip_pct'].median():.1f}%" if len(f) else "—")

quest_tab, understand_tab, explore_tab, study_tab, tell_tab, source_tab = st.tabs(["Q: Question", "U: Understand", "E: Explore", "S: Study", "T: Tell", "Data source"])

with quest_tab:
    st.subheader("Analytical mission")
    st.markdown("""
**Decision context:** Holiday taxi service is affected by shopping, travel, dining, tourism, airport movement, and late-night activity. A city transportation analyst or taxi fleet manager could use this dashboard to understand when demand concentrates, which boroughs and taxi zones dominate the holiday flow, and whether short-distance, payment, fare, and tipping behavior changes across the holiday period.

**Guiding questions:**
1. When were yellow taxi pickups busiest during Christmas Eve and Christmas Day?
2. What do typical holiday trips look like in distance, duration, and fare amount?
3. How do payment methods relate to recorded tipping behavior?
4. Which pickup and dropoff taxi zones and borough-to-borough flows dominate holiday taxi movement?
5. Are there unusual trips that should be interpreted carefully before making operational conclusions?
""")

with understand_tab:
    st.subheader("Data audit")
    c1, c2 = st.columns([1, 1])
    missing = df.isna().mean().reset_index()
    missing.columns = ["Column", "Missing share"]
    c1.plotly_chart(px.bar(missing, x="Column", y="Missing share", title="Missing values by column"), use_container_width=True)
    audit = pd.DataFrame({
        "Metric": ["Original rows", "Original columns", "Rows after current filters", "Duplicate rows", "Earliest pickup", "Latest pickup"],
        "Value": [f"{len(df):,}", f"{df.shape[1]:,}", f"{len(f):,}", f"{df.duplicated().sum():,}", str(df.tpep_pickup_datetime.min()), str(df.tpep_pickup_datetime.max())]
    })
    c2.dataframe(audit, hide_index=True, use_container_width=True)
    st.caption("The plausible trip filter is optional so viewers can compare raw vs. cleaned patterns rather than silently hiding data-quality issues. Taxi zone labels are joined from the TLC lookup table using pickup and dropoff location IDs.")

with explore_tab:
    st.subheader("Individual variable patterns")
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.histogram(f, x="trip_distance", nbins=60, title="Trip distance distribution", labels={"trip_distance":"Trip distance (miles)"}), use_container_width=True)
    c2.plotly_chart(px.histogram(f, x="total_amount", nbins=60, title="Total fare distribution", labels={"total_amount":"Total amount ($)"}), use_container_width=True)
    c3, c4 = st.columns(2)
    pay_counts = f["payment_label"].value_counts().reset_index()
    pay_counts.columns = ["Payment type", "Trips"]
    c3.plotly_chart(px.bar(pay_counts, x="Payment type", y="Trips", title="Trips by payment type"), use_container_width=True)
    c4.plotly_chart(px.box(f, x="pickup_day", y="trip_duration_min", points=False, title="Trip duration by pickup day", labels={"trip_duration_min":"Duration (min)", "pickup_day":"Pickup day"}), use_container_width=True)

with study_tab:
    st.subheader("Relationships and geographic patterns")
    hourly = f.groupby(["pickup_date", "pickup_hour"], as_index=False).agg(trips=("VendorID", "count"), median_fare=("total_amount", "median"), median_tip_pct=("tip_pct", "median"))
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.line(hourly, x="pickup_hour", y="trips", color="pickup_date", markers=True, title="Pickup demand by hour", labels={"pickup_hour":"Pickup hour", "trips":"Trips"}), use_container_width=True)
    sample = f.sample(min(len(f), 20000), random_state=42) if len(f) > 0 else f
    c2.plotly_chart(px.scatter(sample, x="trip_distance", y="total_amount", color="payment_label", opacity=0.35, title="Fare vs. trip distance", labels={"trip_distance":"Distance (miles)", "total_amount":"Total amount ($)", "payment_label":"Payment"}), use_container_width=True)
    c3, c4 = st.columns(2)
    c3.plotly_chart(px.box(f, x="payment_label", y="tip_pct", points=False, title="Recorded tip percentage by payment type", labels={"tip_pct":"Tip as % of fare", "payment_label":"Payment"}), use_container_width=True)
    top_n = st.slider("Number of top pickup/dropoff zones to show", 5, 25, 10)
    pu = f["PU_Label"].value_counts().head(top_n).reset_index(); pu.columns=["Pickup zone", "Trips"]
    do = f["DO_Label"].value_counts().head(top_n).reset_index(); do.columns=["Dropoff zone", "Trips"]
    c4.plotly_chart(px.bar(pu, x="Trips", y="Pickup zone", orientation="h", title=f"Top {top_n} pickup zones"), use_container_width=True)
    st.plotly_chart(px.bar(do, x="Trips", y="Dropoff zone", orientation="h", title=f"Top {top_n} dropoff zones"), use_container_width=True)
    borough_flow = f.groupby(["PU_Borough", "DO_Borough"], as_index=False).size().rename(columns={"size":"Trips"})
    st.plotly_chart(px.density_heatmap(borough_flow, x="PU_Borough", y="DO_Borough", z="Trips", histfunc="sum", title="Trips by pickup borough and dropoff borough", labels={"PU_Borough":"Pickup borough", "DO_Borough":"Dropoff borough", "Trips":"Trips"}), use_container_width=True)

with tell_tab:
    st.subheader("Synthesis for a non-technical audience")
    st.markdown("""
The holiday taxi story is about **timing, trip purpose, geography, and payment behavior**. Use the date/time and borough filters to compare Christmas Eve with Christmas Day and to isolate specific travel flows. The hourly chart shows when demand concentrates; the distribution charts show whether the holiday period is dominated by short local rides or longer airport-style trips; the zone charts translate numeric TLC IDs into more readable borough and neighborhood-style names; and the payment/tipping charts show that payment method strongly affects what can be observed about tips because cash tips are often not recorded in the meter data.

**Recommendations:**
- Use hourly pickup patterns to plan driver availability during the strongest demand windows.
- Use pickup/dropoff zone and borough-flow charts to identify holiday travel concentrations.
- Treat extreme distances, very long durations, zero-distance trips, and negative fares as audit items rather than immediate operational conclusions.
- Avoid interpreting cash tips as true zero generosity; the dataset mainly records electronic tip amounts.
""")

with source_tab:
    st.subheader("Data source, access, and sustainability")
    st.markdown("""
**Trip data source:** NYC Taxi & Limousine Commission / NYC Open Data, 2018 Yellow Taxi Trip Data.  
**Original trip-data URL:** https://data.cityofnewyork.us/Transportation/2018-Yellow-Taxi-Trip-Data/t29m-gskq  
**Taxi zone lookup:** TLC taxi zone lookup table, used to translate `PULocationID` and `DOLocationID` into borough, zone, and service-zone fields.  
**Lookup-table NYC.gov source URL:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
**Access date for this project file:** June 2026.  
**Dataset scope used here:** Christmas Eve–Christmas Day 2018 yellow taxi trips, one row per taxi trip.  
**Terms:** Public NYC Open Data / City of New York terms of use should be reviewed before publication.  
**Terms-of-Use URL:** https://www.nyc.gov/main/terms-of-use
**Refresh plan:** Download newer TLC monthly yellow taxi trip records, filter to the same holiday dates or another target period, apply the same feature-engineering steps, and keep joining against the TLC taxi zone lookup table so geography remains readable.
""")
    st.dataframe(df.head(25), use_container_width=True)

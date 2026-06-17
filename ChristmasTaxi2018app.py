import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="NYC Yellow Taxi Holiday Dashboard",
    page_icon="🚕",
    layout="wide"
)

TAXI_ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(
        "taxi_christmas_2018_cleaned.csv.gz",
        parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"]
    )

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

st.title("NYC Yellow Taxi Trips: Christmas Eve–Christmas Day 2018")

st.markdown("""
Help the Metropolitan Transit Association understand NYC yellow taxi trips from Christmas Eve and Christmas Day 2018.
""")

st.sidebar.header("Filters")

pickup_borough_options = sorted(df["PU_Borough"].dropna().unique())
dropoff_borough_options = sorted(df["DO_Borough"].dropna().unique())

selected_pickup_boroughs = st.sidebar.multiselect(
    "Pickup Location",
    pickup_borough_options,
    default=pickup_borough_options
)

selected_dropoff_boroughs = st.sidebar.multiselect(
    "Dropoff Location",
    dropoff_borough_options,
    default=dropoff_borough_options
)

max_distance = float(np.nanpercentile(df["trip_distance"], 99))

distance_range = st.sidebar.slider(
    "Trip distance range (miles)",
    0.0,
    max(1.0, round(max_distance, 1)),
    (0.0, max(1.0, round(max_distance, 1)))
)

f = df[
    (df["trip_distance"].between(distance_range[0], distance_range[1])) &
    (df["PU_Borough"].isin(selected_pickup_boroughs)) &
    (df["DO_Borough"].isin(selected_dropoff_boroughs))
].copy()

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Trips", f"{len(f):,}")
k2.metric("Median distance", f"{f['trip_distance'].median():.2f} mi" if len(f) else "—")
k3.metric("Median duration", f"{f['trip_duration_min'].median():.1f} min" if len(f) else "—")
k4.metric("Median total fare", f"${f['total_amount'].median():.2f}" if len(f) else "—")
k5.metric("Median tip %", f"{f['tip_pct'].median():.1f}%" if len(f) else "—")

overview_tab, patterns_tab, source_tab = st.tabs([
    "Overview & FAQ",
    "Trip Patterns",
    "Data Source"
])

with overview_tab:
    st.subheader("How does NYC move during Christmas?")

    st.markdown("""
    Holiday taxi travel can be affected by shopping, airport trips, tourism, restaurants,
    and late-night activity.

    This dashboard focuses on three questions:

    1. When were yellow taxi pickups busiest?
    2. What did typical trips look like in distance and fare amount?
    3. Which pickup and dropoff zones appeared most often?

    Some taxi records may have unusual distances, durations, or fare amounts, so the results
    should be read as general patterns rather than perfect measurements.
    """)

with patterns_tab:
    st.subheader("Trip patterns")

    st.markdown("""
    This section looks at taxi activity during Christmas Eve and Christmas Day. The charts show
    when pickups were busiest, how trip distance and fare amounts were distributed, how fare relates
    to distance, and which pickup and dropoff zones appeared most often.
    """)

    c1, c2 = st.columns(2)

    c1.plotly_chart(
        px.histogram(
            f,
            x="trip_distance",
            nbins=60,
            title="Trip distance distribution",
            labels={"trip_distance": "Trip distance (miles)"}
        ),
        use_container_width=True
    )

    c2.plotly_chart(
        px.histogram(
            f,
            x="total_amount",
            nbins=60,
            title="Total fare distribution",
            labels={"total_amount": "Total amount ($)"}
        ),
        use_container_width=True
    )

    hourly = f.groupby(
        ["pickup_date", "pickup_hour"],
        as_index=False
    ).agg(
        trips=("VendorID", "count")
    )

    c3, c4 = st.columns(2)

    c3.plotly_chart(
        px.line(
            hourly,
            x="pickup_hour",
            y="trips",
            color="pickup_date",
            markers=True,
            title="Pickup demand by hour",
            labels={
                "pickup_hour": "Pickup hour",
                "trips": "Trips"
            }
        ),
        use_container_width=True
    )

    sample = f.sample(min(len(f), 20000), random_state=42) if len(f) > 0 else f

    c4.plotly_chart(
        px.scatter(
            sample,
            x="trip_distance",
            y="total_amount",
            opacity=0.35,
            title="Fare vs. trip distance",
            labels={
                "trip_distance": "Distance (miles)",
                "total_amount": "Total amount ($)"
            }
        ),
        use_container_width=True
    )

    top_n = 10

    pu = f["PU_Label"].value_counts().head(top_n).reset_index()
    pu.columns = ["Pickup zone", "Trips"]

    do = f["DO_Label"].value_counts().head(top_n).reset_index()
    do.columns = ["Dropoff zone", "Trips"]

    c5, c6 = st.columns(2)

    c5.plotly_chart(
        px.bar(
            pu,
            x="Trips",
            y="Pickup zone",
            orientation="h",
            title="Top 10 pickup zones"
        ),
        use_container_width=True
    )

    c6.plotly_chart(
        px.bar(
            do,
            x="Trips",
            y="Dropoff zone",
            orientation="h",
            title="Top 10 dropoff zones"
        ),
        use_container_width=True
    )

with source_tab:
    st.subheader("Data source and notes")

    st.markdown("""
    **Trip data source:** NYC Taxi & Limousine Commission / NYC Open Data, 2018 Yellow Taxi Trip Data.  
    **Original trip-data URL:** [2018 Yellow Taxi Trip Data](https://data.cityofnewyork.us/Transportation/2018-Yellow-Taxi-Trip-Data/t29m-gskq)  
    **Taxi zone lookup:** TLC taxi zone lookup table, used to translate pickup and dropoff location IDs.  
    **Lookup-table NYC.gov source URL:** [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)  
    **Access dates:** June 15 and June 16, 2026.  
    **Dataset used here:** Christmas Eve–Christmas Day 2018 yellow taxi trips.  
    **Terms of Use:** [NYC Terms of Use](https://www.nyc.gov/main/terms-of-use)  

    To refresh the data, a newer TLC yellow taxi dataset could be downloaded from NYC Open Data and joined
    with the taxi zone lookup table in the same way.
    """)

    st.caption(
        "The dashboard includes the filtered taxi records, so unusual trips may still appear in some charts."
    )

    audit = pd.DataFrame({
        "Metric": [
            "Original rows",
            "Original columns",
            "Rows after current filters",
            "Duplicate rows",
            "Earliest pickup",
            "Latest pickup"
        ],
        "Value": [
            f"{len(df):,}",
            f"{df.shape[1]:,}",
            f"{len(f):,}",
            f"{df.duplicated().sum():,}",
            str(df.tpep_pickup_datetime.min()),
            str(df.tpep_pickup_datetime.max())
        ]
    })

    st.dataframe(audit, hide_index=True, use_container_width=True)

    st.subheader("Sample rows")
    st.dataframe(df.head(25), use_container_width=True)

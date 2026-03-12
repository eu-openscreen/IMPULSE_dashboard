# Last Updated: 12 Mar, 2026

"""Display Page for OpenScreen Impulse"""

import json
import re
from urllib.request import urlopen

import pandas as pd

# import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pycountry
import streamlit as st
from PIL import Image
from streamlit_agraph import Config, Edge, Node, agraph

# from streamlit_searchbox import st_searchbox

st.set_page_config(
    layout="wide",
    page_title="EU OpenScreen-Impulse",
    page_icon="🇪🇺",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
        <style>
            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 1.5rem;
                padding-left: 5rem;
                padding-right: 5rem;
            }
            .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {font-size:1.3rem;}
        </style>
        """,
    unsafe_allow_html=True,
)  # .block-conatiner controls the padding of the page, .stTabs controls the font size of the text in the tabs

st.markdown(
    "<h1 style='text-align: center; color: #FF8E1C;'> EU OpenScreen-Impulse </h1> <br>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h2 style='text-align: center; color: #1B3C67;'> European Infrastructure of Open Screening Platforms for Chemical Biology </h2> <br>",
    unsafe_allow_html=True,
)
bg_image = Image.open("images/pages/openscreen_impulse_background.png")
resized_bg = bg_image.resize((1800, 300))
st.image(resized_bg, use_container_width=True)


# bg_image = Image.open("images/pages/openscreen_impulse_background.png")

# max_width = 1200
# aspect_ratio = bg_image.height / bg_image.width
# new_height = int(max_width * aspect_ratio)

# resized_bg = bg_image.resize((max_width, new_height))

# st.image(resized_bg)


st.markdown("## IMPULSE Initiative")
st.markdown(
    "**IMPULSE** seeks to enhance EU-OPENSCREEN's role as a premier platform for chemical biology and early drug discovery in Europe "
    "with regards to the key areas of **enhancing service catalogue**, **improving standards**, **fueling community engagement**, and **ensuring sustainability**"
)
st.markdown(
    "Additional information about **EU-OpenScreen IMPULSE** can be found [here.](https://www.eu-openscreen.eu/impulse-overview.html)"
)
st.markdown(
    """
    ### Key Focus Areas

    **🎯 Validating pharmacology using advanced disease models & genetic screens:** Open call for proposal to develop new models in uncovered disease areas or improve existing models using better assay technology.

    **🎯 New chemical modalities:** Demonstrator projects started, covering fluorescent probes, traceless proximity probes and quenched activity-based probes, targeted proteins/RNA degraders, chemically diverse covalent and allosteric protein modulators and multitarget compounds.

    **🎯 Data Reproducibility & Operational Standards:** Mapping of data standard across EU-OPENSCREEN partner sites ongoing. Preparation of an interlaboratory comparison to assess and improve reproducibility and consistency across EU-OPENSCREEN screening partners.

    **🎯 ML/AI for prediction of modes of action**  with cell painting and small molecule data.

    """,
    unsafe_allow_html=True,
)

# st.markdown("### Cataloging Screening")
# st.image("images/pages/openscreen_cataloguing_screening.png")
# st.caption("Cataloging Screening Visualized based on Site, Types and Assays.")

# df = pd.read_csv('data/Cataloguing screening.csv')

# df = df.loc[df['Site'].notna()]

# st.write(df)

############################### STREAMLIT SEARCHBOX UTILS START #######################################

_search_df = pd.read_csv(
    "data/Cataloguing screening_v2.csv"
)  # This version was made on 12th March.
_search_df = _search_df.loc[_search_df["Type"].notna()]
_search_cols = [
    "Site",
    "Type",
    "Model organism",
    "Cell type",
    "Assay format",
]


def search_data(searchterm: str):
    if searchterm:
        suggestions = []
        for col in _search_cols:
            matches = _search_df[col].dropna().unique()
            suggestions.extend(
                [str(v) for v in matches if searchterm.lower() in str(v).lower()]
            )
        return sorted(set(suggestions))[:10]
    return []


############################### STREAMLIT SEARCHBOX UTILS END #######################################


############################### PARTNERS AND SITES MAP START #######################################
st.markdown("### Partners and Sites Location")
with urlopen(
    "https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/GeoJSON/europe.geojson"
) as response:
    countries = json.load(response)  # GeoJSON countries

excel_data = pd.read_csv("data/Cataloguing screening_v2.csv")
excel_data = excel_data.dropna(subset=["Site", "Partner Site Country"])

map_data = (
    excel_data.groupby("Partner Site Country")["Site"]
    .agg(
        **{
            "Partner counts": "nunique",
            "Site Names": lambda x: "<br>• " + "<br>• ".join(sorted(x.unique())),
        }
    )
    .reset_index()
    .rename(columns={"Partner Site Country": "Location"})
)


def get_country_full_name(code):
    try:
        return pycountry.countries.get(alpha_2=code).name
    except (AttributeError, LookupError):
        return code


map_data["Full Country Name"] = map_data["Location"].apply(get_country_full_name)

fig = px.choropleth_mapbox(
    map_data,
    geojson=countries,
    locations="Location",
    color="Full Country Name",
    color_discrete_sequence=px.colors.qualitative.Set2,
    mapbox_style="open-street-map",
    zoom=3,
    center={"lat": 51.0057, "lon": 13.7274},
    opacity=0.7,
    featureidkey="properties.ISO2",
    custom_data=["Full Country Name", "Partner counts", "Site Names"],
)

fig.update_traces(
    hovertemplate=(
        "<b>Country: %{customdata[0]}</b><br>"
        "<b>Total Partner Sites: %{customdata[1]}</b>"
        "%{customdata[2]}"
        "<extra></extra>"
    )
)
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    showlegend=False,
)

st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
############################### PARTNERS AND SITES MAP END #######################################

# selected = st_searchbox(
#     search_function=search_data,
#     key="searchbox",
#     placeholder="Look up specific partner, screening type, model organism, assay format or biological system...",
# )

st.markdown(
    "**The tabs below present the expertise information in a structured format, allowing you to easily navigate through the different sections using the corresponding dropdown menu.**"
)

selected = None
# tab1, tab2, tab3, tab4 = st.tabs(
#     ["Cataloging Screening", "Screening Types", "KG overview", "Data standard heatmap"]
# )
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Cataloging Screening",
        "Screening Types",
        "Disease Areas",
        "Data Standard Heatmap",
    ]
)

with tab1:
    st.header("Overview of partners", divider="gray")

    df = pd.read_csv("data/Cataloguing screening_v2.csv")

    df = df.loc[df["Type"].notna()]

    institutes = sorted(df["Site"].unique())
    selected_institute = st.selectbox(
        "Select a partner institute", institutes, key="overview"
    )

    filtered_df = df[df["Site"] == selected_institute].copy()

    # st.dataframe(filtered_df)

    # st.dataframe(filtered_df[['Type','Model organism','Cell type','Assay format']], use_container_width=True, hide_index=True)

    screen_counts = filtered_df["Type"].value_counts().to_frame().reset_index()

    # st.dataframe(screen_counts)

    col = st.columns(2, gap="large")
    with col[0]:
        fig = px.pie(
            values=screen_counts["count"],
            names=screen_counts["Type"],
            title=f"Types of screening for {selected_institute}",
            labels={"names": "Type", "values": "Number of screens"},
        )

        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Number of screens: %{value}<extra></extra>"
        )
        st.plotly_chart(fig)

    with col[1]:
        st.write("**Details of screening types**")
        #        st.dataframe(filtered_df[['Type','Model organism','Cell type','Assay format']], use_container_width=True, hide_index=True)
        _display_df = filtered_df[
            ["Type", "Model organism", "Cell type", "Assay format"]
        ]
        st.dataframe(_display_df, use_container_width=True, hide_index=True)
        # st.write("**Need to contact the partner?**")
        # csv_file = filtered_df.to_csv(index=False).encode("utf-8")
        # st.download_button(
        #     "Press to Download",
        #     csv_file,
        #     f"{institutes}_file.csv",
        #     "text/csv",
        #     key="download-csv",
        # )

    st.subheader("Overview of screening details")

    # pivot = df.groupby(['Site', 'Assay format']).size().unstack(fill_value=0)

    # # Create the matplotlib figure and axis
    # fig, ax = plt.subplots(figsize=(12, 6))
    # pivot.plot(kind='bar', stacked=False, ax=ax)
    # plt.title('Distribution of Assay Format Usage per Site')
    # plt.xlabel('Site')
    # plt.ylabel('Number of Experiments')
    # plt.xticks(rotation=45)
    # plt.legend(title='Assay format')
    # plt.tight_layout()

    # st.pyplot(fig)

    # For example:
    # df = pd.read_csv("your_data.csv")

    df = filtered_df[["Type", "Model organism", "Cell type", "Assay format"]]

    df_cols = sorted(["Model organism", "Cell type", "Assay format"])
    # st.write(temp_col)

    # break
    selected_column = st.selectbox("Select an attribute", df_cols)

    # filtered_df = df[df["Partner Site Name"] == selected_institute]

    # type_counts = df[selected_column].value_counts().reset_index()
    # type_counts.columns = [selected_column, 'Count']

    # fig1 = px.bar(type_counts,
    #     x=selected_column,
    #     y='Count',
    #     title=f'Number of {selected_column.lower()}s per screening',
    #     labels={'Count': f'Number of {selected_column.lower()}s', 'Type': 'Screening Type'},
    #     text='Count',
    #     height=600)

    # fig1.update_traces(textposition='outside')
    # fig1.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=-45)

    # st.plotly_chart(fig1, use_container_width=True)

    # grouped = df.groupby(['Type', selected_column]).size().reset_index(name='count')

    # fig2 = px.bar(grouped,
    #     x='Type',
    #     y='count',
    #     color=selected_column,
    #     barmode='group',
    #     title=f'{selected_column} Distribution per Type',
    #     labels={'count': f'Number of {selected_column}s', 'Type': 'Type', selected_column: selected_column})

    # fig2.update_layout(xaxis_tickangle=-45)

    # st.plotly_chart(fig2, use_container_width=True)

    total_counts = df[selected_column].value_counts().reset_index()
    total_counts.columns = [selected_column, "count"]

    fig = px.pie(
        total_counts,
        values="count",
        names=selected_column,
        title=f"Overall {selected_column} Distribution",
        hole=0.3,
    )

    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Overview of screening types", divider="gray")

    df = pd.read_csv("data/Cataloguing screening_v2.csv")

    df = df.loc[df["Type"].notna()]

    screening_types = sorted(df["Type"].unique())
    selected_screening_type = st.selectbox(
        "Select a screening type", screening_types, key="screening_overview"
    )

    filtered_df = df[df["Type"] == selected_screening_type].copy()

    screen_counts = filtered_df["Site"].value_counts().to_frame().reset_index()

    col = st.columns(2, gap="large")
    with col[0]:
        fig = px.pie(
            values=screen_counts["count"],
            names=screen_counts["Site"],
            title=f"Partner institutes for {selected_screening_type}",
            labels={"names": "Partner Institute", "values": "Number of screens"},
        )

        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>Number of screens: %{value}<extra></extra>"
        )
        st.plotly_chart(fig)

    with col[1]:
        st.write("**Details of partner institutes**")

        viz_option = st.radio(
            "Choose a visualization type:",
            ["Chart View", "Table View"],
            horizontal=True,
            key="partner_viz_option",
        )

        if viz_option == "Chart View":
            treemap_data = []
            for _, row in filtered_df.iterrows():
                treemap_data.append(
                    {
                        "Site": row["Site"],
                        "Model_organism": row["Model organism"],
                        "Cell_type": row["Cell type"],
                        "Assay_format": row["Assay format"],
                        "Count": 1,
                    }
                )

            treemap_df = pd.DataFrame(treemap_data)
            treemap_df = treemap_df.dropna()

            fig_treemap = px.treemap(
                treemap_df,
                path=[
                    px.Constant("All Partners"),
                    "Site",
                    "Model_organism",
                    "Cell_type",
                    "Assay_format",
                ],
                values="Count",
                color="Site",
                title=f"Treemap of Screening Details for {selected_screening_type}",
                color_discrete_sequence=px.colors.qualitative.Set2,
                height=500,
            )

            fig_treemap.update_traces(
                hovertemplate="<b>%{label}</b><br>Path: %{currentPath}<br><extra></extra>",
                textinfo="label+value",
                textfont_size=12,
                textfont_color="white",
                marker=dict(line=dict(width=2, color="white"), colorscale="viridis"),
            )

            fig_treemap.update_layout(
                font=dict(family="Arial, sans-serif", size=12, color="#2F3E46"),
                paper_bgcolor="white",
                plot_bgcolor="white",
                title=dict(
                    font=dict(size=16, color="#2F3E46"), x=0.5, xanchor="center"
                ),
            )

            st.plotly_chart(fig_treemap, use_container_width=True)

        else:
            _display_df2 = filtered_df[
                [
                    "Site",
                    "Model organism",
                    "Cell type",
                    "Assay format",
                ]
            ]
            st.dataframe(_display_df2, use_container_width=True, hide_index=True)

    st.subheader("Overview of screening details")

    df = filtered_df[["Site", "Model organism", "Cell type", "Assay format"]]

    df_cols = sorted(["Model organism", "Cell type", "Assay format"])
    selected_column = st.selectbox(
        "Select an attribute", df_cols, key="screening_attribute"
    )

    type_counts = df[selected_column].value_counts().reset_index()
    type_counts.columns = [selected_column, "Count"]

    # fig1 = px.bar(type_counts,
    #     x=selected_column,
    #     y='Count',
    #     title=f'Number of {selected_column.lower()}s for {selected_screening_type}',
    #     labels={'Count': f'Number of {selected_column.lower()}s', selected_column: selected_column},
    #     text='Count',
    #     height=600)

    # fig1.update_traces(textposition='outside')
    # fig1.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=-45)

    # st.plotly_chart(fig1, use_container_width=True)

    # grouped = df.groupby(['Site', selected_column]).size().reset_index(name='count')

    # fig2 = px.bar(grouped,
    #     x='Site',
    #     y='count',
    #     color=selected_column,
    #     barmode='group',
    #     title=f'{selected_column} Distribution per Partner Institute',
    #     labels={'count': f'Number of {selected_column}s', 'Site': 'Partner Institute', selected_column: selected_column})

    # fig2.update_layout(xaxis_tickangle=-45)

    # st.plotly_chart(fig2, use_container_width=True)

    total_counts = df[selected_column].value_counts().reset_index()
    total_counts.columns = [selected_column, "count"]

    fig = px.pie(
        total_counts,
        values="count",
        names=selected_column,
        title=f"Overall {selected_column} Distribution for {selected_screening_type}",
        hole=0.3,
    )

    st.plotly_chart(fig, use_container_width=True)

# with tab3:
#     # Set Page Configuration
#     # st.set_page_config(layout="wide")

#     st.title("IMPULSE partners overview")

#     df = pd.read_csv("data/Cataloguing screening_3.csv")

#     df = df.loc[df["Type"].notna()]

#     cols = ["Site", "Type", "Model organism", "Cell type", "Assay format"]

#     df = df[cols]

#     mappings = {
#         "Site": "red",
#         "Type": "blue",
#         "Model organism": "cyan",
#         "Cell type": "green",
#         "Assay format": "purple",
#     }

#     nodes_2, edges_2 = [], []
#     node_unique_2 = set()

#     def _add_node(name, col):
#         if pd.notna(name) and name not in node_unique_2:
#             node_unique_2.add(name)
#             nodes_2.append(Node(id=name, label=name, color=mappings[col]))

#     def _add_edge(src, tgt):
#         if pd.notna(src) and pd.notna(tgt):
#             _add_node(src, next(c for c in cols if src in df[c].values))
#             _add_node(tgt, next(c for c in cols if tgt in df[c].values))
#             edges_2.append(Edge(source=src, target=tgt))

#     for _, row in df.iterrows():
#         _add_edge(row["Site"], row["Type"])
#         _add_edge(row["Type"], row["Assay format"])
#         _add_edge(row["Assay format"], row["Cell type"])
#         _add_edge(row["Cell type"], row["Model organism"])

#     config = Config(
#         width=1500,
#         height=900,
#         directed=True,
#         nodeHighlightBehavior=True,
#         highlightColor="#F7A7A6",
#         collapsible=False,
#         node={"labelProperty": "label"},
#         link={"labelProperty": "label", "renderLabel": False},
#         hierarchical=True,
#         hierarchicalSorting=True,
#         layout={
#             "hierarchical": {
#                 "enabled": True,
#                 "levelSeparation": 150,
#                 "nodeSpacing": 100,
#                 "treeSpacing": 200,
#                 "direction": "UD",  # UD for top to bottom
#                 "sortMethod": "directed",
#             }
#         },
#         zoom=1.2,
#     )

#     agraph(nodes=nodes_2, edges=edges_2, config=config)

#     st.subheader("Overview per partner")

#     partner = sorted(df["Site"].unique())
#     selected_partner = st.selectbox("Select a partner institute", partner, key="kg")

#     filtered_df = df[df["Site"] == selected_partner]

#     nodes, edges = [], []
#     node_unique = set()

#     def _add_node_p(name, col):
#         if pd.notna(name) and name not in node_unique:
#             node_unique.add(name)
#             nodes.append(Node(id=name, label=name, color=mappings[col]))

#     def _add_edge_p(src, src_col, tgt, tgt_col):
#         if pd.notna(src) and pd.notna(tgt):
#             _add_node_p(src, src_col)
#             _add_node_p(tgt, tgt_col)
#             edges.append(Edge(source=src, target=tgt, type="CURVE_SMOOTH"))

#     for _, row in filtered_df.iterrows():
#         _add_edge_p(row["Site"], "Site", row["Type"], "Type")
#         _add_edge_p(row["Type"], "Type", row["Assay format"], "Assay format")
#         _add_edge_p(row["Assay format"], "Assay format", row["Cell type"], "Cell type")
#         _add_edge_p(
#             row["Cell type"], "Cell type", row["Model organism"], "Model organism"
#         )

#     config = Config(
#         width=2000,
#         height=1080,
#         directed=True,
#         nodeHighlightBehavior=True,
#         highlightColor="#F7A7A6",
#         collapsible=False,
#         node={"labelProperty": "label"},
#         link={"labelProperty": "label", "renderLabel": False},
#         hierarchical=False,
#         hierarchicalSorting=True,
#         layout={
#             "hierarchical": {
#                 "enabled": True,
#                 "levelSeparation": 150,
#                 "nodeSpacing": 100,
#                 "treeSpacing": 200,
#                 "direction": "UD",  # UD for top to bottom
#                 "sortMethod": "directed",
#             }
#         },
#         zoom=1.2,  # Adjust as needed
#     )

#     agraph(nodes=nodes, edges=edges, config=config)

with tab3:
    st.header("Disease Area Overview", divider="gray")

    df_disease = pd.read_csv("data/Cataloguing screening_v2.csv")
    df_disease = df_disease.loc[df_disease["Type"].notna()]
    df_disease["Disease Area"] = df_disease["Disease Area"].str.strip()
    df_disease = df_disease.dropna(subset=["Disease Area"])

    disease_areas = sorted(df_disease["Disease Area"].unique())
    renamed_diseases = {
        "Infectious": "Infectious Diseases",
        "Metabolic": "Metabolic Disorders",
        "Neurological": "Neurological Disorders",
    }
    selected_disease = st.selectbox(
        "Select a disease area", disease_areas, key="disease_area_select"
    )

    filtered_disease = df_disease[df_disease["Disease Area"] == selected_disease].copy()

    # st.subheader(f"Partners & Screening Types for {selected_disease} Disease Area")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        treemap_partners = []
        for _, row in filtered_disease.iterrows():
            treemap_partners.append(
                {
                    "Disease Area": row["Disease Area"],
                    "Site": row["Site"],
                    "Type": row["Type"],
                    "Count": 1,
                }
            )
        treemap_partners_df = pd.DataFrame(treemap_partners).dropna()

        fig_partners = px.treemap(
            treemap_partners_df,
            path=[px.Constant(selected_disease), "Site", "Type"],
            values="Count",
            color="Site",
            title=f"Partners & Screening Types for {selected_disease} Disease Area",
            color_discrete_sequence=px.colors.qualitative.Set2,
            height=500,
        )
        fig_partners.update_traces(
            hovertemplate="<b>%{label}</b><br>Path: %{currentPath}<br>Count: %{value}<extra></extra>",
            textinfo="label+value",
            textfont_size=12,
        )
        fig_partners.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig_partners, use_container_width=True)

    with col2:
        treemap_assay = []
        for _, row in filtered_disease.iterrows():
            treemap_assay.append(
                {
                    "Disease Area": row["Disease Area"],
                    "Model organism": row["Model organism"],
                    "Cell type": row["Cell type"],
                    "Assay format": row["Assay format"],
                    "Count": 1,
                }
            )
        treemap_assay_df = pd.DataFrame(treemap_assay).dropna()

        fig_assay = px.treemap(
            treemap_assay_df,
            path=[
                px.Constant(selected_disease),
                "Model organism",
                "Cell type",
                "Assay format",
            ],
            values="Count",
            color="Model organism",
            title=f"Model Organisms, Cell Types & Assay Formats for {selected_disease} Disease Area",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            height=500,
        )
        fig_assay.update_traces(
            hovertemplate="<b>%{label}</b><br>Path: %{currentPath}<br>Count: %{value}<extra></extra>",
            textinfo="label+value",
            textfont_size=12,
        )
        # fig_assay.update_traces(
        #     hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
        #     textinfo="label+value",
        # )
        fig_assay.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig_assay, use_container_width=True)

    #    st.subheader(f"Full Screening Detail for {selected_disease} Disease Area")

    treemap_full = []
    for _, row in filtered_disease.iterrows():
        treemap_full.append(
            {
                "Site": row["Site"],
                "Type": row["Type"],
                "Model organism": row["Model organism"],
                "Cell type": row["Cell type"],
                "Assay format": row["Assay format"],
                "Count": 1,
            }
        )
    treemap_full_df = pd.DataFrame(treemap_full).dropna()

    fig_full = px.treemap(
        treemap_full_df,
        path=[
            px.Constant(selected_disease),
            "Site",
            "Type",
            "Model organism",
            "Cell type",
            "Assay format",
        ],
        values="Count",
        color="Site",
        title=f"Complete Screening Hierarchy for {selected_disease} Disease Area",
        color_discrete_sequence=px.colors.qualitative.Set2,
        height=600,
    )
    fig_full.update_traces(
        hovertemplate="<b>%{label}</b><br>Path: %{currentPath}<br>Count: %{value}<extra></extra>",
        textinfo="label+value",
        textfont_size=12,
    )
    fig_full.update_layout(margin=dict(t=50, l=10, r=10, b=10))
    st.plotly_chart(fig_full, use_container_width=True)


with tab4:
    # st.header('Heatmap of IMPULSE survey')

    st.markdown(
        "Following is a preliminary survey result that was conducted among the partners and institutes in the IMPULSE project. A detailed overview of the survery  will be provided soon."
    )

    data = pd.read_excel(
        "data/Task 5.1 - Mapping data standards survey_cs.xlsx",
        sheet_name="Survey",
        header=1,
    )

    data = data[data["Unnamed: 72"] != "not filled"]
    # st.write(data.head(5))

    # st.write(data.columns)

    cols = [
        "Name",
        "Data Management Plan",
        "Laboratory Information Management System (LIMS) [yes/no]",
        "Electronic Laboratory Notebook (ELN) [yes/no]",
        "Lab data steward [yes/no]",
        "Are your data FAIR? [yes/no]",
        "BioAssay Ontology (BAO) [yes/no]",
        "Relevant [yes/no].3",
        "Relevant [yes/no].4",
        "Relevant [yes/no].5",
        "Relevant [yes/no].6",
        "Relevant [yes/no].7",
        "Relevant [yes/no].8",
        "Scripting [yes/no]",
        "Version control system [yes/no]",
    ]

    data = data[cols]

    data = data.reset_index(drop=True)

    data = data.fillna("no")

    # st.write(data.head(2))

    def yes_no_replace(val):
        if isinstance(val, str):
            if re.match(r"^yes\b", val, flags=re.IGNORECASE):
                return "yes"
            else:
                return "no"
        else:
            return "no"

    cols_to_replace = [col for col in data.columns if col != "Name"]

    data[cols_to_replace] = data[cols_to_replace].applymap(yes_no_replace)

    cols = [
        "Name",
        "DMP",
        "LIMS",
        "ELN",
        "Data steward",
        "FAIR",
        "BAO",
        "Protein",
        "Nucleic acid",
        "Organism",
        "Analytical data",
        "Imaging data",
        "OMICs data",
        "Scripting",
        "Version control",
    ]

    data.columns = cols

    # st.write(data)

    feature_data = data.drop("Name", axis=1)

    z = feature_data.replace({"yes": 1, "no": 0}).values.T

    colorscale = [[0, "blue"], [1, "cyan"]]

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=data["Name"],
            y=feature_data.columns,
            colorscale=colorscale,
            colorbar=dict(tickvals=[0, 1], ticktext=["No", "Yes"]),
            showscale=True,
        )
    )

    fig.update_layout(
        title="Heat map of IMPULSE survey based on availability of data and resources",
        xaxis_title="Institutes",
        yaxis_title="Survey answers",
        xaxis_tickangle=45,
        height=700,
    )

    st.plotly_chart(fig, use_container_width=True)

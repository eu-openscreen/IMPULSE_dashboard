"""EU-OPENSCREEN advanced disease model catalogue"""

import base64
from html import escape
from io import BytesIO
from urllib.parse import urlencode

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

SITE_URL = "https://www.eu-openscreen.eu/index.html"
ACCESS_URL = "https://www.eu-openscreen.eu/index.php?id=21"
DATA_FILE = "data/Cataloguing screening_v2.csv"  # This version was made on 12th March.
NOT_SPECIFIED = "Not specified"

SECTIONS = {
    "overview": "Overview",
    "find": "Find a model",
    "sites": "Site profiles",
    "genetic": "Genetic screens",
    "about": "About the data",
}

# Filters on the Find a model page. Every filter accepts several values.
FACETS = {
    "site": "Partner site",
    "area": "Disease area",
    "purpose": "Purpose",
    "format": "Assay format",
    "organism": "Organism",
    "system": "Biological system",
    "readout": "Readout",
    "plate": "Plate format",
    "scale": "Scale (data points)",
}
SCALE_ORDER = ["<100", "100-1k", "1-5k", "5-20k", ">20k"]

COUNTRIES = {
    "CZ": "Czechia",
    "DE": "Germany",
    "ES": "Spain",
    "FI": "Finland",
    "PL": "Poland",
    "PT": "Portugal",
    "SE": "Sweden",
}

# Hero background settings.
HERO_IMAGE = "images/pages/euos_background.png"
HERO_ZOOM = 1.0  # 1.0 fits the whole image height; above 1 zooms in, below 1 zooms out
HERO_POSITION = "right top"  # which part of the image stays in view, e.g. "center", "right top"
HERO_FADE = "30%"  # how much of the image's left side fades into HERO_COLOR
HERO_COLOR = "#0F2E64"  # matches the image's edge colour, so the fade has no visible seam
HERO_SHOW_IMAGE = False  # the interactive site map replaces the dotted background map

# Partner site locations for the hero map: (latitude, longitude, city, label position).
SITE_LOCATIONS = {
    "CBCS-KI": (59.348, 18.023, "Stockholm", "bottom left"),
    "CIPF": (39.478, -0.408, "Valencia", "middle right"),
    "FMP": (52.628, 13.505, "Berlin", "top center"),
    "Fraunhofer ITMP": (53.580, 9.970, "Hamburg", "top center"),
    "HZI": (52.284, 10.556, "Braunschweig", "bottom center"),
    "IBCH PAS": (52.404, 16.950, "Poznan", "middle right"),
    "IMG": (50.035, 14.430, "Prague", "bottom center"),
    "MEDINA": (37.160, -3.600, "Granada", "bottom center"),
    "UH-FIMM": (60.205, 24.960, "Helsinki", "middle right"),
    "USC": (42.880, -8.545, "Santiago de Compostela", "top center"),
    "UTU": (60.450, 22.290, "Turku", "top center"),
    "i3S": (41.177, -8.600, "Porto", "middle left"),
}

# Right-hand column and highlight boxes of the "Why use advanced disease models" section.
MODEL_TYPES = [
    (
        "Advanced 2D models",
        "#F5A21C",
        "Neural, cancer and hiPSC-derived cells in 96- to 1536-well formats, with fluorescence, "
        "luminescence, FRET/BRET, high-content imaging, flow cytometry and impedance readouts.",
        ["HZI", "IMG", "UP-IMTM", "MEDINA", "CIPF", "USC", "UH-FIMM", "UH-PHAR", "UTU", "i3S", "UC", "KI", "UMU"],
    ),
    (
        "Advanced 3D models",
        "#F5A21C",
        "Tumour spheroids, organoids and zebrafish xenografts for cytotoxicity, imaging and viability assays.",
        ["UP-IMTM", "MEDINA", "CIPF", "USC", "UH-FIMM", "UTU", "i3S", "KI", "UMU"],
    ),
    (
        "Co-culture & immune-oncology models",
        "#8FA7C9",
        "Host-pathogen systems, differentiated hiPSC co-cultures and immune-responsive assays "
        "for functional and mechanistic profiling.",
        ["IMG", "UP-IMTM", "CIPF", "USC", "UH-PHAR", "UTU", "i3S", "UMU", "KI"],
    ),
    (
        "Disease-relevant primary & patient-derived cells",
        "#8FA7C9",
        "Rodent neurons, human primary cultures and patient-derived samples, depending on material availability.",
        ["IMG", "UP-IMTM", "MEDINA", "CIPF", "USC", "UH-FIMM", "UTU", "i3S", "UC", "KI"],
    ),
]
HIGHLIGHTS = [
    (">400", "patient samples analysed with drug sensitivity and resistance testing", "UH-FIMM, Helsinki"),
    ("Zebrafish", "embryo assays for neurological, cardiovascular and oncology phenotyping and toxicity testing", "UTU, Turku"),
    ("BSL-3", "cell culture and infection models for viral and bacterial infection biology", "HZI, Braunschweig"),
]

# st.set_page_config(
#     layout="wide",
#     page_title="EU-OPENSCREEN: Impulse Dashboard",
#     page_icon="🇪🇺",
# )

st.set_page_config(
    layout="wide",
    page_title="EU-OPENSCREEN: Impulse Dashboard",
    page_icon="🇪🇺",
    initial_sidebar_state="collapsed",
)


############################### DATA START #######################################


@st.cache_data
def image_data_uri(path, max_width, image_format):
    """Downscale an image once and return it as a data URI for use in HTML."""
    image = Image.open(path)
    if image.width > max_width:
        image = image.resize(
            (max_width, round(image.height * max_width / image.width)),
            Image.LANCZOS,
        )
    if image_format == "JPEG":
        image = image.convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format=image_format, quality=92)
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/{image_format.lower()};base64,{encoded}"


def assay_formats(row):
    """Return every assay format of a model, with the 3D subtype as its own value."""
    formats = []
    for column in ["Assay Design (1)", "Assay Design (2)"]:
        if pd.notna(row[column]) and row[column] not in formats:
            formats.append(row[column])
    subtype = row["if 3D: assay type"]
    if "3D" in formats and pd.notna(subtype):
        formats.append(f"3D {subtype.split('/')[0].lower()}")
    return tuple(formats) or (NOT_SPECIFIED,)


@st.cache_data
def load_catalogue():
    """Read the catalogue, clean blank cells and add the columns the pages use."""
    df = pd.read_csv(DATA_FILE)
    df = df.dropna(subset=["Site"]).copy()
    # Blank cells in the catalogue are sometimes a non-breaking space or a dash.
    for column in df.columns:
        df[column] = df[column].str.strip().replace({"": pd.NA, "-": pd.NA})
    df["Assay readout (3)"] = df["Assay readout (3)"].replace({"other": "Other"})

    readout_columns = ["Assay readout", "Assay readout (2)", "Assay readout (3)"]
    readouts = df[readout_columns].apply(
        lambda row: tuple(dict.fromkeys(row.dropna())), axis=1
    )
    formats = df.apply(assay_formats, axis=1)
    details = df["Model and modification details (free text)"]

    df["Disease area"] = df["Primary Disease Area"].fillna(NOT_SPECIFIED)
    df["Model details"] = details.map(capitalise, na_action="ignore").fillna(NOT_SPECIFIED)
    df["Assay format"] = formats.map(
        lambda values: ", ".join(v for v in values if not v.startswith("3D ")) + (
            f" ({values[-1][3:]})" if values[-1].startswith("3D ") else ""
        )
    )
    df["Readouts"] = readouts.map(lambda values: ", ".join(values) or NOT_SPECIFIED)
    df["Availability"] = df["Available to the User"].map(
        lambda value: "Available to users" if value == "Yes" else "Ask the site"
    )

    single_value_facets = {
        "site": "Site",
        "area": "Primary Disease Area",
        "purpose": "Type",
        "organism": "Model Organism",
        "system": "Biological System",
        "plate": "Plate density",
        "scale": "Data Points",
    }
    for key, column in single_value_facets.items():
        df[f"f_{key}"] = df[column].fillna(NOT_SPECIFIED).map(lambda value: (value,))
    df["f_format"] = formats
    df["f_readout"] = readouts.map(lambda values: values or (NOT_SPECIFIED,))

    df["search_text"] = df.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    return df


def catalogue_columns(df):
    """Columns of the original CSV, without the helper columns added above."""
    return [column for column in pd.read_csv(DATA_FILE, nrows=0).columns if column in df]


def facet_options(df, key):
    """All values of a filter, most common first, with Not specified last."""
    counts = df[f"f_{key}"].explode().value_counts()
    if key == "scale":
        options = [value for value in SCALE_ORDER if value in counts]
        options += [value for value in counts.index if value not in options]
    else:
        options = list(counts.index)
    if NOT_SPECIFIED in options:
        options.remove(NOT_SPECIFIED)
        options.append(NOT_SPECIFIED)
    return options


def value_or_default(row, column, default=NOT_SPECIFIED):
    return default if pd.isna(row[column]) else row[column]


def capitalise(text):
    """Capitalise free text that starts with a lowercase word, but leave terms like iPSC alone."""
    return text[0].upper() + text[1:] if text[:2].islower() else text


def label(text):
    """Escape Markdown in a button label, so values like ">20k" show as written."""
    for character in "\\`*_[]~$<>#+-|:":
        text = text.replace(character, f"\\{character}")
    return text


############################### DATA END #######################################


############################### STATE AND NAVIGATION START #######################################


def init_state(df):
    """Read the starting state from the URL once, then keep it in session state."""
    state, params = st.session_state, st.query_params
    if "section" not in state:
        page = params.get("page", "overview")
        state.section = page if page in SECTIONS else "overview"
    if "fm_selected" not in state:
        state.fm_selected = {
            key: [value for value in params.get_all(f"fm_{key}") if value in facet_options(df, key)]
            for key in FACETS
        }
    if "fm_search" not in state:
        state.fm_search = params.get("fm_q", "")
    if "fm_available" not in state:
        state.fm_available = params.get("fm_available") == "1"
    if "fm_model" not in state:
        model = params.get("fm_model", "")
        state.fm_model = int(model) if model.isdigit() else None
    if "sp_site" not in state:
        sites = df["Site"].value_counts().index
        site = params.get("site")
        state.sp_site = site if site in sites else sites[0]

    # Streamlit drops the value of a widget that is not drawn in a run. Saving these
    # again keeps the search, checkbox and site choice while another section is open.
    for key in ["fm_search", "fm_available", "sp_site"]:
        state[key] = state[key]

    section = state.section
    if section == "overview":
        params.pop("page", None)
    else:
        params["page"] = section
    if section != "find":
        for key in [key for key in params if key.startswith("fm_")]:
            del params[key]
    if section != "sites":
        params.pop("site", None)


def go_to(section):
    st.session_state.section = section


def open_find(site=None, area=None):
    """Open Find a model with only the given site and disease area selected."""
    state = st.session_state
    state.fm_selected = {key: [] for key in FACETS}
    if site:
        state.fm_selected["site"] = [site]
    if area:
        state.fm_selected["area"] = [area]
    state.fm_search = ""
    state.fm_available = False
    state.fm_model = None
    state.section = "find"


def open_site(site):
    st.session_state.sp_site = site
    st.session_state.section = "sites"


############################### STATE AND NAVIGATION END #######################################


############################### LAYOUT START #######################################


def render_styles(section):
    background = image_data_uri(HERO_IMAGE, 2000, "JPEG")
    st.markdown(
        """
        <style>
            .block-container {padding-top: 2.5rem; padding-bottom: 2rem;}
            .lp-button {display: inline-block; background: #F5A21C; color: #0E2A5C !important; font-weight: 600;
                padding: 0.6rem 1.1rem; text-decoration: none !important; border: 1px solid #F5A21C;}
            .lp-button:hover {filter: brightness(1.05);}
            .lp-outline {background: transparent; color: white !important; border-color: white;}
            .st-key-lp_orange button, [class*="st-key-lp_orange_"] button {background: #F5A21C; border: 1px solid #F5A21C;
                border-radius: 0; padding: 0.6rem 1.1rem;}
            .st-key-lp_orange button p, [class*="st-key-lp_orange_"] button p {color: #0E2A5C; font-weight: 600;}
            .st-key-lp_orange button:hover, [class*="st-key-lp_orange_"] button:hover {filter: brightness(1.05);
                border-color: #F5A21C;}

            .st-key-lp_nav {background: white; padding: 0.6rem 1.5rem;}
            /* Freeze the menu bar: it stays at the top while the page scrolls under it */
            div:has(> .st-key-lp_nav), .st-key-lp_nav {position: sticky; top: var(--nav-top, 3.75rem); z-index: 999;}
            .st-key-lp_nav {box-shadow: 0 2px 6px rgba(14, 42, 92, 0.08);}
            #who-offers-what, #catalogue-coverage {scroll-margin-top: 9rem;}
            .st-key-lp_nav img {height: 2rem;}
            .st-key-lp_nav [class*="st-key-nav_"] button p {color: #1B3C67; font-size: 0.9rem;}
            .st-key-lp_nav [class*="st-key-nav_"] button:hover p {text-decoration: underline;}
            @media (max-width: 640px) {
                .st-key-lp_nav [data-testid="stHorizontalBlock"] {flex-flow: row wrap; gap: 0.25rem 1.25rem;}
                .st-key-lp_nav [data-testid="stColumn"] {width: auto !important; flex: 0 0 auto !important; min-width: 0 !important;}
                .st-key-lp_nav [data-testid="stColumn"]:first-child {width: 100% !important;}
            }

            .st-key-lp_hero {position: relative; overflow: hidden; background: var(--hero-color); color: white;
                padding: clamp(2.5rem, 7vw, 6rem) clamp(1.25rem, 5vw, 4.5rem); gap: 0;}
            /* The image sits at full hero height on the right, and its left edge fades into the hero colour. */
            .st-key-lp_hero::before {content: ""; position: absolute; top: 0; right: 0; bottom: 0;
                aspect-ratio: 2933 / 1650; background: var(--hero-image) var(--hero-position) / cover no-repeat;
                transform: scale(var(--hero-zoom)); transform-origin: var(--hero-position);
                -webkit-mask-image: linear-gradient(to right, transparent, black var(--hero-fade));
                mask-image: linear-gradient(to right, transparent, black var(--hero-fade));}
            .st-key-lp_hero > div {position: relative;}
            .st-key-lp_hero_actions [data-testid="stHorizontalBlock"] {width: fit-content; gap: 0.75rem;}
            .st-key-lp_hero_actions [data-testid="stColumn"] {width: auto; flex: 0 0 auto; min-width: 0;}
            .st-key-lp_hero_map {padding: 0;}
            /* Fade the map's edges into the banner colour */
            .st-key-lp_hero_map .stPlotlyChart {
                -webkit-mask-image: linear-gradient(to right, transparent, black 15%, black 85%, transparent),
                    linear-gradient(to bottom, transparent, black 10%, black 90%, transparent);
                -webkit-mask-composite: source-in;
                mask-image: linear-gradient(to right, transparent, black 15%, black 85%, transparent),
                    linear-gradient(to bottom, transparent, black 10%, black 90%, transparent);
                mask-composite: intersect;}
            .lp-map-note {font-size: 0.8rem; opacity: 0.75; text-align: right; margin-top: -0.5rem;}
            .lp-hero-text {max-width: 36rem;}
            .lp-eyebrow {display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem;
                letter-spacing: 0.08em; text-transform: uppercase;}
            .lp-eyebrow i {width: 0.5rem; height: 0.5rem; border-radius: 50%; background: #F5A21C;}
            .lp-eyebrow i:nth-child(3) {background: #8FA7C9; margin-right: 0.5rem;}
            .lp-title {font-size: clamp(2rem, 4vw, 3rem); font-weight: 600; line-height: 1.15; margin: 1rem 0;}
            .lp-intro {font-size: 1rem; line-height: 1.6; opacity: 0.9; margin-bottom: 1.5rem;}
            .lp-stats {display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: 1.5rem;
                background: #33527A; color: white; padding: 2rem clamp(1.25rem, 5vw, 4.5rem);}
            .lp-stats strong {display: block; color: #F5A21C; font-size: 2.5rem; font-weight: 600; line-height: 1.2;}
            .lp-stats span {font-size: 0.9rem;}

            .pg-banner {background: #0E2A5C; color: white; padding: 2rem 2.5rem; margin-bottom: 1rem;}
            .pg-banner strong {display: block; font-size: 2rem; font-weight: 600;}
            .pg-banner span {display: block; max-width: 48rem; margin-top: 0.4rem; opacity: 0.85;}

            .why-eyebrow {font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.7;
                margin-top: 2.5rem;}
            .why-title {font-size: clamp(1.6rem, 3vw, 2.1rem); font-weight: 600; line-height: 1.2; margin: 0.5rem 0 0.75rem;}
            .why-rule {width: 3rem; height: 3px; background: #F5A21C; margin-bottom: 1.25rem;}
            .why-left p, .why-left li {font-size: 0.95rem; line-height: 1.6;}
            .why-left ul {padding-left: 1.2rem; margin-bottom: 1rem;}
            .why-link {display: inline-block; padding: 0.6rem 0; color: inherit !important; font-size: 0.9rem; font-weight: 600;}
            .st-key-why_actions [data-testid="stHorizontalBlock"] {width: fit-content; gap: 1.25rem; align-items: center;}
            .st-key-why_actions [data-testid="stColumn"] {width: auto; flex: 0 0 auto; min-width: 0;}
            .why-type {display: grid; grid-template-columns: 0.6rem 1fr; gap: 0 0.85rem; padding: 1.1rem 0;
                border-bottom: 1px solid rgba(128, 128, 128, 0.25);}
            .why-type:last-child {border-bottom: none;}
            .why-type i {width: 0.55rem; height: 0.55rem; border-radius: 50%; margin-top: 0.45rem;}
            .why-type strong {display: block; font-size: 1rem; margin-bottom: 0.3rem;}
            .why-type p {font-size: 0.9rem; line-height: 1.5; opacity: 0.85; margin: 0 0 0.5rem;}
            .why-right {margin-top: 2.5rem;}
            .why-boxes {display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
                gap: 1.5rem; margin: 2rem 0 1rem;}
            .why-box {background: #0E2A5C; color: white; padding: 1.5rem;}
            .why-box strong {display: block; color: #F5A21C; font-size: 2rem; font-weight: 600; line-height: 1.2;
                margin-bottom: 0.5rem;}
            .why-box p {font-size: 0.9rem; line-height: 1.5; margin: 0 0 0.75rem;}
            .why-box span {font-size: 0.75rem; opacity: 0.8;}

            .tags {display: flex; flex-wrap: wrap; gap: 0.3rem;}
            .tags span {background: #DAE5F5; color: #1B3C67; font-size: 0.75rem; padding: 0.1rem 0.45rem;}

            .wow-legend {display: flex; justify-content: flex-end; align-items: center; gap: 0.25rem; font-size: 0.8rem;}
            .wow-legend span {width: 1.5rem; height: 0.75rem;}
            .wow-center {text-align: center; font-size: 0.9rem;}
            .wow-head {text-align: center; font-size: 0.8rem; opacity: 0.8;}
            .st-key-wow_grid, .st-key-wow_grid [data-testid="stHorizontalBlock"] {gap: 2px;}
            .st-key-wow_grid [data-testid="stHorizontalBlock"] {border-bottom: 1px solid rgba(128, 128, 128, 0.2);}
            .st-key-wow_grid button {min-height: 2.4rem; border: none; border-radius: 0;}
            .st-key-wow_grid button p {font-size: 0.9rem;}
            [class*="st-key-wow_site_"] button {justify-content: flex-start;}
            [class*="st-key-wow_site_"] button:hover, [class*="st-key-wow_site_"] button:hover p {color: inherit;
                text-decoration: underline;}
            [class*="st-key-wow_s"] button:hover {filter: brightness(0.92);}
            .wow-shade-1, [class*="st-key-wow_s1_"] button {background: #DAE5F5; color: #1B3C67;}
            .wow-shade-2, [class*="st-key-wow_s2_"] button {background: #A9C1E1; color: #1B3C67;}
            .wow-shade-3, [class*="st-key-wow_s3_"] button {background: #33527A; color: white;}
            .wow-shade-4, [class*="st-key-wow_s4_"] button {background: #0E2A5C; color: white;}
            [class*="st-key-wow_s"] button:hover p {color: inherit;}

            .fm-meta {font-size: 0.8rem; opacity: 0.8;}
            .fm-chips {margin-bottom: 1rem;}
            .fm-record-head {background: #0E2A5C; color: white; padding: 1.25rem;}
            .fm-record-head .fm-title {font-size: 1.3rem; font-weight: 600; margin: 0.4rem 0 0.75rem;}
            .fm-badge {background: #F5A21C; color: #0E2A5C; font-size: 0.75rem; padding: 0.15rem 0.5rem;}
            .fm-row {display: grid; grid-template-columns: 9rem 1fr; gap: 0.75rem; font-size: 0.85rem;
                padding: 0.45rem 0; border-bottom: 1px solid rgba(128, 128, 128, 0.25);}
            .fm-row span:first-child {opacity: 0.7;}
            .fm-row span:last-child {overflow-wrap: anywhere;}
            .fm-actions {display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem;}
            .fm-actions .lp-outline {color: inherit !important; border-color: currentColor;}
            [class*="st-key-fm_facet_"] {flex-direction: row; flex-wrap: wrap; gap: 0.35rem;}
            [class*="st-key-fm_facet_"] > div {width: auto !important;}
            [class*="st-key-fm_facet_"] button {min-height: 0; padding: 0.2rem 0.6rem; border-radius: 0;}
            [class*="st-key-fm_facet_"] button p {font-size: 0.8rem;}
            [class*="st-key-fm_facet_"] button[kind="primary"] {background: #0E2A5C; border-color: #0E2A5C; color: white;}
            [class*="st-key-fm_facet_"] button[kind="secondary"]:hover,
            [class*="st-key-fm_facet_"] button[kind="secondary"]:focus:not(:active) {border-color: #0E2A5C; color: #0E2A5C;}
            [class*="st-key-fm_card_"] {gap: 0.25rem;}
            [class*="st-key-fm_card_"] button {justify-content: flex-start; text-align: left;}
            [class*="st-key-fm_card_"] button p {font-weight: 600; text-align: left;}
            .sp-tiles {display: grid; grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr)); gap: 1rem; margin: 1rem 0;}
            .sp-tiles div {background: #DAE5F5; color: #1B3C67; padding: 0.9rem 1.1rem; font-size: 0.85rem;}
            .sp-tiles strong {display: block; font-size: 1.8rem; font-weight: 600; line-height: 1.2;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <style>
            .st-key-lp_hero {{--hero-image: url({background}); --hero-zoom: {HERO_ZOOM};
                --hero-position: {HERO_POSITION}; --hero-fade: {HERO_FADE}; --hero-color: {HERO_COLOR};}}
            .st-key-nav_{section} button p {{font-weight: 600; border-bottom: 2px solid #F5A21C;}}
            {"" if HERO_SHOW_IMAGE else ".st-key-lp_hero::before {display: none;}"}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_nav():
    logo = image_data_uri("images/pages/euos_logo.png", 800, "PNG")
    with st.container(key="lp_nav"):
        columns = st.columns([2.6, 1, 1.1, 1.1, 1.2, 1.2, 1.5], vertical_alignment="center")
        columns[0].html(
            f'<a href="{SITE_URL}" target="_blank" rel="noopener"><img src="{logo}" alt="EU-OPENSCREEN"></a>'
        )
        for column, (key, label) in zip(columns[1:], SECTIONS.items()):
            column.button(label, key=f"nav_{key}", type="tertiary", on_click=go_to, args=(key,))
        columns[-1].html(
            f'<a class="lp-button" href="{ACCESS_URL}" target="_blank" rel="noopener">Apply for access</a>'
        )


def page_banner(title, text):
    st.html(f'<div class="pg-banner"><strong>{title}</strong><span>{text}</span></div>')


def tags(values):
    return f'<div class="tags">{"".join(f"<span>{escape(str(value))}</span>" for value in values)}</div>'


############################### LAYOUT END #######################################


############################### OVERVIEW START #######################################


def site_map(df):
    """Europe map with one orange pin per partner site, sized by its number of models."""
    sites = df.groupby(["Site", "Partner Site Country"]).agg(
        models=("Site", "size"),
        areas=("Disease area", lambda values: ", ".join(values[values != NOT_SPECIFIED].value_counts().index[:3])),
    ).reset_index()
    sites = sites[sites["Site"].isin(SITE_LOCATIONS)]
    location = sites["Site"].map(SITE_LOCATIONS)
    country = sites["Partner Site Country"].map(lambda code: COUNTRIES.get(code, code))
    figure = go.Figure(
        go.Scattergeo(
            lat=location.str[0],
            lon=location.str[1],
            text=sites["Site"],
            customdata=list(zip(sites["Site"], location.str[2], country, sites["models"], sites["areas"])),
            mode="markers+text",
            textposition=location.str[3].tolist(),
            textfont={"color": "white", "size": 11},
            marker={
                "size": 9 + sites["models"] ** 0.5 * 4,
                "color": "#F5A21C",
                "opacity": 0.95,
                "line": {"color": "white", "width": 1.5},
            },
            selected={"marker": {"opacity": 1}},
            unselected={"marker": {"opacity": 0.95}},
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>%{customdata[1]}, %{customdata[2]}<br>"
                "%{customdata[3]} models<br>Main areas: %{customdata[4]}<br>"
                "<i>Click to open the site profile</i><extra></extra>"
            ),
        )
    )
    figure.update_geos(
        projection_type="mercator",
        lonaxis_range=[-26, 51],
        lataxis_range=[32, 67.5],
        resolution=50,
        showland=True,
        landcolor="#22467F",
        showocean=True,
        oceancolor=HERO_COLOR,
        showlakes=True,
        lakecolor=HERO_COLOR,
        showcountries=True,
        countrycolor="#5B7BAE",
        countrywidth=0.6,
        coastlinecolor="#5B7BAE",
        coastlinewidth=0.6,
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
    )
    figure.update_layout(
        height=430,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        dragmode="pan",
        clickmode="event+select",
        hoverlabel={"bgcolor": "white", "font": {"color": "#0E2A5C"}},
        showlegend=False,
    )
    return figure


def open_site_from_map():
    points = st.session_state.hero_map.selection.points
    if points:
        open_site(points[0]["customdata"][0])


def render_overview(df):
    with st.container(key="lp_hero"):
        text, chart = st.columns([1, 1.1], vertical_alignment="center", gap="large")
        with text:
            st.html(
                '<div class="lp-hero-text">'
                '<div class="lp-eyebrow"><i></i><i></i><i></i>Capabilities catalogue</div>'
                '<div class="lp-title">Advanced disease models for compound validation</div>'
                '<div class="lp-intro">Find patient-derived, iPSC-derived, gene-edited and 3D models at '
                "EU-OPENSCREEN partner sites, for screening, hit validation, profiling and "
                "mechanism-of-action studies.</div></div>"
            )
            with st.container(key="lp_hero_actions"):
                actions = st.columns(2, vertical_alignment="center")
                with actions[0], st.container(key="lp_orange_hero"):
                    st.button("Find a model", key="hero_find", on_click=open_find)
                actions[1].html(
                    '<a class="lp-button lp-outline" href="#who-offers-what" target="_self">See the overview</a>'
                )
        with chart, st.container(key="lp_hero_map"):
            st.plotly_chart(
                site_map(df),
                key="hero_map",
                on_select=open_site_from_map,
                selection_mode="points",
                use_container_width=True,
                config={"displayModeBar": False, "scrollZoom": False},
            )
            st.html('<div class="lp-map-note">Pin size shows the number of models. Click a pin to open the site.</div>')

    stats = [
        (len(df), "models and assay set-ups"),
        (df["Site"].nunique(), "partner sites"),
        (df["Partner Site Country"].nunique(), "countries"),
        (df["Primary Disease Area"].nunique(), "disease areas"),
    ]
    st.html(
        '<div class="lp-stats">'
        + "".join(f"<div><strong>{value}</strong><span>{label}</span></div>" for value, label in stats)
        + "</div>"
    )

    render_why_section(df)
    render_who_offers_what(df)


def render_why_section(df):
    left, right = st.columns(2, gap="large")
    with left:
        st.html(
            '<div class="why-left">'
            '<div class="why-eyebrow" id="catalogue-coverage">What the catalogue covers</div>'
            '<div class="why-title">Why use advanced disease models?</div>'
            '<div class="why-rule"></div>'
            "<p>Many promising compounds fail in later stages of drug discovery because standard cell lines "
            "do not reflect how a disease works in patients. Advanced disease models, such as patient-derived "
            "cells, iPSC-derived cells, gene-edited cells, 3D cultures, organoids and co-cultures, reproduce "
            "disease-specific mechanisms more closely. Results from these models are more likely to predict "
            "how a compound behaves in vivo.</p>"
            "<p><strong>EU-OPENSCREEN partner sites offer these models for several stages of a project:</strong></p>"
            "<ul>"
            "<li>Screening: smaller primary screens in complex biological systems.</li>"
            "<li>Validation: confirming hits from large high-throughput campaigns in a disease-relevant setting.</li>"
            "<li>Profiling: testing selected compounds across several models, donors or patient samples.</li>"
            "<li>Mechanism of action: studying how a compound works, together with genetic and proteomic approaches.</li>"
            "</ul>"
            "<p>Projects range from a few compounds profiled across many models to screens of up to 100,000 "
            "compounds. Our Partner Sites can advise on model selection, controls and assay format before you apply.</p>"
            "</div>"
        )
        with st.container(key="why_actions"):
            actions = st.columns(2, vertical_alignment="center")
            with actions[0], st.container(key="lp_orange_why"):
                st.button(f"Browse {len(df)} models", key="why_find", on_click=open_find)
            actions[1].html('<a class="why-link" href="#who-offers-what" target="_self">See the overview &rarr;</a>')
    with right:
        st.html(
            '<div class="why-right">'
            + "".join(
                f'<div class="why-type"><i style="background: {color}"></i><div>'
                f"<strong>{title}</strong><p>{text}</p>{tags(sites)}</div></div>"
                for title, color, text, sites in MODEL_TYPES
            )
            + "</div>"
        )
    st.html(
        '<div class="why-boxes">'
        + "".join(
            f'<div class="why-box"><strong>{escape(value)}</strong><p>{text}</p><span>{site}</span></div>'
            for value, text, site in HIGHLIGHTS
        )
        + "</div>"
    )


def render_who_offers_what(df):
    """Site by disease area counts. A cell opens those models in Find a model; a site opens its profile."""
    counts = pd.crosstab(df["Site"], df["Disease area"])
    columns = [
        area
        for area in counts.sum().sort_values(ascending=False, kind="mergesort").index
        if area != NOT_SPECIFIED
    ]
    if NOT_SPECIFIED in counts.columns:
        columns.append(NOT_SPECIFIED)
    site_totals = counts.sum(axis=1).sort_values(ascending=False, kind="mergesort")
    area_totals = counts.sum()
    site_countries = df.groupby("Site")["Partner Site Country"].first()

    def shade(count):
        if count <= 2:
            return 1
        if count <= 5:
            return 2
        if count <= 10:
            return 3
        return 4

    # st.html avoids the negative bottom margin st.markdown adds, which misaligns grid rows.
    def centered(cell, text):
        cell.html(f'<div class="wow-center">{text}</div>')

    st.subheader("Who offers what", anchor="who-offers-what")
    st.markdown(
        "Number of models per partner site and primary disease area. "
        "Select a site to open its profile, or a cell to see those models."
    )
    legend = "".join(f'<span class="wow-shade-{level}"></span>' for level in range(1, 5))
    st.html(f'<div class="wow-legend">Fewer&nbsp;{legend}&nbsp;More</div>')

    weights = [2.2] + [1] * len(columns) + [0.8]
    with st.container(key="wow_grid"):
        header = st.columns(weights, vertical_alignment="bottom")
        header[0].html('<div class="wow-head" style="text-align: left">Partner site</div>')
        for cell, label in zip(header[1:], columns + ["Total"]):
            cell.html(f'<div class="wow-head">{label}</div>')

        for row_number, (site, total) in enumerate(site_totals.items()):
            cells = st.columns(weights, vertical_alignment="center")
            cells[0].button(
                f"**{site}** :gray[{site_countries[site]}]",
                key=f"wow_site_{row_number}",
                type="tertiary",
                on_click=open_site,
                args=(site,),
            )
            for column_number, (cell, column) in enumerate(zip(cells[1:], columns)):
                count = int(counts.loc[site, column])
                if count:
                    cell.button(
                        str(count),
                        key=f"wow_s{shade(count)}_{row_number}_{column_number}",
                        use_container_width=True,
                        on_click=open_find,
                        args=(site, column),
                    )
            centered(cells[-1], f"<strong>{total}</strong>")

        footer = st.columns(weights, vertical_alignment="center")
        footer[0].html("<strong>All sites</strong>")
        for cell, column in zip(footer[1:], columns):
            centered(cell, f"<strong>{area_totals[column]}</strong>")
        centered(footer[-1], f"<strong>{len(df)}</strong>")


############################### OVERVIEW END #######################################


############################### FIND A MODEL START #######################################


@st.fragment
def render_find_a_model(df):
    """Searchable, filterable model list with the full record of the selected model."""
    state = st.session_state
    selected = state.fm_selected
    search = state.fm_search.strip()
    available_only = state.fm_available

    def matches(skip=None):
        mask = df["search_text"].str.contains(search.lower(), regex=False)
        if available_only:
            mask &= df["Available to the User"].eq("Yes")
        for key in FACETS:
            if key != skip and selected[key]:
                wanted = set(selected[key])
                mask &= df[f"f_{key}"].map(lambda values: not wanted.isdisjoint(values))
        return mask

    def toggle_filter(key, value):
        if value in selected[key]:
            selected[key].remove(value)
        else:
            selected[key].append(value)

    def clear_filters():
        open_find()

    def open_model(model_id):
        state.fm_model = model_id

    def publication_links(row):
        if pd.isna(row["Publication Details (doi only)"]):
            return "None listed"
        links = []
        for doi in row["Publication Details (doi only)"].split(";"):
            doi = escape(doi.strip())
            if doi.startswith("10."):
                doi = f'<a href="https://doi.org/{doi}" target="_blank" rel="noopener">{doi}</a>'
            links.append(doi)
        return "<br>".join(links)

    def render_facet(key):
        facet_counts = df.loc[matches(skip=key), f"f_{key}"].explode().value_counts()
        with st.container(key=f"fm_facet_{key}"):
            for number, value in enumerate(facet_options(df, key)):
                count = int(facet_counts.get(value, 0))
                is_selected = value in selected[key]
                st.button(
                    label(f"{value} ({count})"),
                    key=f"fm_option_{key}_{number}",
                    type="primary" if is_selected else "secondary",
                    disabled=count == 0 and not is_selected,
                    on_click=toggle_filter,
                    args=(key, value),
                )

    results = df[matches()]
    selected_model = state.fm_model
    if selected_model not in results.index:
        selected_model = None

    params = {"page": "find"}
    params.update({f"fm_{key}": values for key, values in selected.items() if values})
    if search:
        params["fm_q"] = search
    if available_only:
        params["fm_available"] = "1"
    if selected_model is not None:
        params["fm_model"] = str(selected_model)
    for key in [key for key in st.query_params if key.startswith("fm_")]:
        if key not in params:
            del st.query_params[key]
    for key, value in params.items():
        st.query_params[key] = value

    if selected_model is not None:
        st.markdown(
            f"""
            <style>
                .st-key-fm_card_{selected_model} {{background: #DAE5F5; color: #1B3C67;}}
                .st-key-fm_card_{selected_model} button p {{color: #1B3C67;}}
                .st-key-fm_card_{selected_model} .tags span {{background: white;}}
            </style>
            """,
            unsafe_allow_html=True,
        )

    page_banner(
        "Find an advanced disease model",
        "Combine filters and free-text search. Filters in the same group match any of the selected values.",
    )
    render_facet("site")
    st.write("")

    filter_col, results_col, record_col = st.columns([1.1, 2, 1.6], gap="medium")

    with filter_col:
        st.text_input("Search", key="fm_search", placeholder="e.g. glioblastoma, organoid, KI")
        for key, facet_label in FACETS.items():
            if key == "site":
                continue
            st.markdown(f"**{facet_label}**")
            render_facet(key)
        st.checkbox("Only models confirmed as available to users", key="fm_available")
        st.button("Clear all filters", key="fm_clear", on_click=clear_filters)

    with results_col:
        count_col, export_col, link_col = st.columns([1, 1, 1.5])
        count_col.markdown(
            f"**{len(results)} {'model matches' if len(results) == 1 else 'models match'}**"
        )
        export_col.download_button(
            "Export CSV",
            results[catalogue_columns(df)].to_csv(index=False).encode("utf-8"),
            "eu_openscreen_models.csv",
            "text/csv",
            disabled=results.empty,
        )
        with link_col.popover("Copy link to this search"):
            page_url = (st.context.url or "").split("?")[0]
            st.code(f"{page_url}?{urlencode(params, doseq=True)}", language=None)

        if results.empty:
            st.info("No models match. Remove a filter or change the search.")

        with st.container(height=1000, border=False):
            for model_id, row in results.iterrows():
                with st.container(border=True, key=f"fm_card_{model_id}"):
                    meta = " | ".join(
                        [
                            row["Site"],
                            row["Partner Site Country"],
                            row["Disease area"],
                            value_or_default(row, "Disease/indication (free text)", "Indication not specified"),
                        ]
                    )
                    st.html(f'<div class="fm-meta">{escape(meta)}</div>')
                    st.button(
                        label(row["Model details"]),
                        key=f"fm_open_{model_id}",
                        type="tertiary",
                        on_click=open_model,
                        args=(model_id,),
                    )
                    chips = [
                        value_or_default(row, "Type", "Purpose not specified"),
                        row["Model Organism"],
                        value_or_default(row, "Biological System", "System not specified"),
                        "Format not specified" if row["Assay format"] == NOT_SPECIFIED else row["Assay format"],
                    ]
                    st.html(f'<div class="fm-chips">{tags(chips)}</div>')

    with record_col:
        if selected_model is None:
            st.info("Select a model title to open its full record.")
            return

        row = df.loc[selected_model]
        is_available = row["Available to the User"] == "Yes"
        data_points = row["Data Points"]
        details_column = next(column for column in df.columns if column.startswith("Additional Details"))
        fields = [
            ("Disease area", row["Disease area"]),
            ("Indication", value_or_default(row, "Disease/indication (free text)")),
            ("Tissue of origin", value_or_default(row, "Tissue of origin (free text)")),
            ("Purpose", value_or_default(row, "Type")),
            ("Organism", row["Model Organism"]),
            ("Biological system", value_or_default(row, "Biological System")),
            ("Model details", row["Model details"]),
            ("Cell lines", value_or_default(row, "Cell line name(s) (free text)")),
            ("Co-culture", value_or_default(row, "Co-culture?")),
            ("Assay format", row["Assay format"]),
            ("Plate format", value_or_default(row, "Plate density")),
            ("Readout", row["Readouts"]),
            ("Assay information", value_or_default(row, "Additional assay information (free text)")),
            ("Typical scale", NOT_SPECIFIED if pd.isna(data_points) else f"{data_points} data points"),
            ("Screening mode", value_or_default(row, "Screening Mode")),
            ("Measurement type", value_or_default(row, "Measurement Type")),
            ("Additional details", value_or_default(row, details_column)),
            ("Availability", row["Availability"]),
            ("Availability notes", value_or_default(row, "Comments regarding the availability")),
        ]
        rows_html = "".join(
            f'<div class="fm-row"><span>{label}</span><span>{escape(value)}</span></div>'
            for label, value in fields
        )
        rows_html += (
            '<div class="fm-row"><span>Publications</span>'
            f"<span>{publication_links(row)}</span></div>"
        )
        badge = '<span class="fm-badge">Available to users</span>' if is_available else ""
        country = COUNTRIES.get(row["Partner Site Country"], row["Partner Site Country"])
        st.html(
            '<div class="fm-record-head">'
            f'<div class="fm-meta">{escape(row["Site"])} | {escape(country)}</div>'
            f'<div class="fm-title">{escape(row["Model details"])}</div>{badge}</div>'
            f"{rows_html}"
            '<div class="fm-actions">'
            f'<a class="lp-button" href="{SITE_URL}" target="_blank" rel="noopener">Request access</a>'
            f'<a class="lp-button lp-outline" href="{SITE_URL}" target="_blank" rel="noopener">Contact the site</a>'
            "</div>"
        )


############################### FIND A MODEL END #######################################


############################### SITE PROFILES START #######################################


def render_site_profiles(df):
    page_banner(
        "Site profiles",
        "What each partner site offers. Select a site to see all of its models and assay set-ups.",
    )
    site_counts = df["Site"].value_counts()
    site = st.selectbox(
        "Partner site",
        site_counts.index,
        key="sp_site",
        format_func=lambda value: f"{value} ({site_counts[value]} models)",
    )
    st.query_params["site"] = site

    site_df = df[df["Site"] == site]
    code = site_df["Partner Site Country"].iloc[0]
    st.subheader(f"{site}, {COUNTRIES.get(code, code)}")
    tiles = [
        (len(site_df), "models and assay set-ups"),
        (site_df["Primary Disease Area"].nunique(), "disease areas"),
        (site_df["Type"].nunique(), "purposes"),
        ((site_df["Available to the User"] == "Yes").sum(), "confirmed available to users"),
    ]
    st.html(
        '<div class="sp-tiles">'
        + "".join(f"<div><strong>{value}</strong>{label}</div>" for value, label in tiles)
        + "</div>"
    )

    area_col, purpose_col = st.columns(2)
    with area_col:
        st.markdown("**Disease areas**")
        areas = site_df["Disease area"].value_counts()
        st.html(tags(f"{area} ({count})" for area, count in areas.items()))
    with purpose_col:
        st.markdown("**Purposes**")
        purposes = site_df["Type"].fillna(NOT_SPECIFIED).value_counts()
        st.html(tags(f"{purpose} ({count})" for purpose, count in purposes.items()))

    st.markdown("**Models and assay set-ups**")
    table = site_df.rename(
        columns={
            "Disease/indication (free text)": "Indication",
            "Type": "Purpose",
            "Model Organism": "Organism",
            "Biological System": "Biological system",
            "Readouts": "Readout",
            "Plate density": "Plate format",
            "Data Points": "Scale (data points)",
        }
    )[
        [
            "Disease area",
            "Indication",
            "Model details",
            "Purpose",
            "Organism",
            "Biological system",
            "Assay format",
            "Readout",
            "Plate format",
            "Scale (data points)",
            "Availability",
        ]
    ].fillna(NOT_SPECIFIED)
    st.dataframe(table, use_container_width=True, hide_index=True)

    with st.container(key="lp_orange_site"):
        st.button(
            f"Open the {len(site_df)} {site} models in Find a model",
            key="sp_find",
            on_click=open_find,
            args=(site,),
        )


############################### SITE PROFILES END #######################################


############################### GENETIC SCREENS AND ABOUT START #######################################


def render_genetic_screens(df):
    page_banner(
        "Genetic screens",
        "CRISPR, RNAi and other genetic screening capabilities at EU-OPENSCREEN partner sites.",
    )
    st.info(
        "Genetic screening capabilities are not part of the current catalogue file yet. "
        "This section will list them once partner sites have reported them."
    )
    edited = df[
        df["search_text"].str.contains(r"crispr|cas9|gene.edit|knock.?in|knock.?out", regex=True)
    ]
    if edited.empty:
        return
    st.markdown(f"**Gene-edited models already in the catalogue ({len(edited)})**")
    st.dataframe(
        edited.rename(columns={"Type": "Purpose", "Model Organism": "Organism"})[
            ["Site", "Disease area", "Model details", "Purpose", "Organism", "Assay format", "Availability"]
        ].fillna(NOT_SPECIFIED),
        use_container_width=True,
        hide_index=True,
    )


def render_about(df):
    page_banner(
        "About the data",
        "Where the catalogue comes from and how to read it.",
    )
    st.markdown(
        f"""
**Source.** The catalogue is collected from EU-OPENSCREEN partner sites as part of the IMPULSE project
(WP3, advanced disease models). This page reads `{DATA_FILE}`, which lists {len(df)} models and assay
set-ups from {df["Site"].nunique()} partner sites in {df["Partner Site Country"].nunique()} countries.

**One row is one model or assay set-up** at one partner site. A site can list the same model several times
when it runs it in different formats, for example in 2D and 3D, or for different purposes.

**How to read the fields**

- **Disease area** is the primary disease area the site gave for the model. **Indication** is the more
  specific disease, as free text.
- **Purpose** is what the model is used for: primary screening, hit follow-up, disease profiling, cell
  phenotyping, toxicity or safety testing, or mechanistic studies.
- **Assay format** is 2D, 3D or suspension culture. For 3D models it also gives the type, for example
  organoid or spheroid.
- **Scale** is the typical number of data points per project.
- **Not specified** means the site left the field empty. It does not mean the answer is no.
- **Availability**: "Available to users" means the site confirmed the model can be offered to external
  users. Everything else reads "Ask the site", because an empty answer does not mean the model is
  unavailable.

**Using a model.** Access goes through the EU-OPENSCREEN application process. Partner sites can advise on
model selection, controls and assay format before you apply.
"""
    )
    st.download_button(
        "Download the full catalogue (CSV)",
        df[catalogue_columns(df)].to_csv(index=False).encode("utf-8"),
        "eu_openscreen_catalogue.csv",
        "text/csv",
    )


############################### GENETIC SCREENS AND ABOUT END #######################################


catalogue = load_catalogue()
init_state(catalogue)
render_styles(st.session_state.section)
render_nav()

page = st.session_state.section
if page == "overview":
    render_overview(catalogue)
elif page == "find":
    render_find_a_model(catalogue)
elif page == "sites":
    render_site_profiles(catalogue)
elif page == "genetic":
    render_genetic_screens(catalogue)
else:
    render_about(catalogue)

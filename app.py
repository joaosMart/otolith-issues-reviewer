"""Otolith Annotation Tool — Streamlit app."""

import streamlit as st
import folium
from streamlit_folium import st_folium

from hf_data import load_metadata, load_image
from sheets import connect, get_annotator_names, load_annotations, save_annotation
from image_utils import adjust_image, clahe_enhancement

# --- Page config ---
st.set_page_config(page_title="Otolith Annotation Tool", layout="wide")

# --- Secrets ---
HF_TOKEN = st.secrets["HF_TOKEN"]
HF_REPO_ID = st.secrets["HF_REPO_ID"]
SHEET_NAME = st.secrets["SHEET_NAME"]
GCP_INFO = dict(st.secrets["gcp_service_account"])


# --- Cached data loading ---
@st.cache_data(ttl=300)
def get_metadata():
    return load_metadata(HF_REPO_ID, HF_TOKEN)


@st.cache_resource
def get_worksheet():
    return connect(GCP_INFO, SHEET_NAME)


# --- Init session state ---
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.selected_age = None
    st.session_state.uncertain = False
    st.session_state.brightness = 0
    st.session_state.contrast = 0
    st.session_state.clahe_on = False

metadata = get_metadata()
worksheet = get_worksheet()
total_images = len(metadata)

# Deferred annotation load (after submit auto-advance)
if st.session_state.get("_needs_annotation_load"):
    del st.session_state._needs_annotation_load
    _current = metadata[st.session_state.current_index]
    _ann = st.session_state.get("annotations", {}).get(_current["image_id"])
    if _ann:
        st.session_state.selected_age = _ann["age"]
        st.session_state.uncertain = _ann["uncertain"]
    else:
        st.session_state.selected_age = None
        st.session_state.uncertain = False


# --- Navigation functions ---
def go_prev():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        _load_existing_annotation()


def go_next():
    if st.session_state.current_index < total_images - 1:
        st.session_state.current_index += 1
        _load_existing_annotation()


def _load_existing_annotation():
    """Pre-fill age/uncertain if this image was already annotated."""
    current = metadata[st.session_state.current_index]
    ann = st.session_state.annotations.get(current["image_id"])
    if ann:
        st.session_state.selected_age = ann["age"]
        st.session_state.uncertain = ann["uncertain"]
    else:
        st.session_state.selected_age = None
        st.session_state.uncertain = False


# --- Keyboard navigation (arrow keys) ---
# Inject JavaScript to capture arrow key presses
st.components.v1.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.key === 'ArrowLeft') {
            const buttons = doc.querySelectorAll('[data-testid="stButton"] button');
            buttons.forEach(btn => {
                if (btn.innerText.includes('Prev')) btn.click();
            });
        } else if (e.key === 'ArrowRight') {
            const buttons = doc.querySelectorAll('[data-testid="stButton"] button');
            buttons.forEach(btn => {
                if (btn.innerText.includes('Next')) btn.click();
            });
        }
    });
    </script>
    """,
    height=0,
)


# --- Annotator selection ---
existing_names = get_annotator_names(worksheet)

if existing_names:
    st.sidebar.subheader("Returning annotator")
    selected = st.sidebar.selectbox("Select your name", existing_names, index=None, placeholder="Choose...")
else:
    selected = None

st.sidebar.subheader("New annotator")
new_name = st.sidebar.text_input("Enter your name")

if new_name:
    annotator = new_name
elif selected:
    annotator = selected
else:
    annotator = None

if not annotator:
    st.warning("Please select or enter your name in the sidebar to begin annotating.")
    st.stop()

# --- Load annotations for this annotator ---
if "annotator_loaded" not in st.session_state or st.session_state.annotator_loaded != annotator:
    st.session_state.annotations = load_annotations(worksheet, annotator)
    st.session_state.annotator_loaded = annotator
    st.session_state.current_index = 0
    st.session_state.selected_age = None
    st.session_state.uncertain = False
    st.session_state.brightness = 0
    st.session_state.contrast = 0
    st.session_state.clahe_on = False
    # Jump to first unannotated image
    for i, row in enumerate(metadata):
        if row["image_id"] not in st.session_state.annotations:
            st.session_state.current_index = i
            break

# --- Check completion ---
if "annotations" in st.session_state and len(st.session_state.annotations) >= total_images:  # total_images
    st.balloons()
    st.markdown(
        "<h1 style='text-align:center;margin-top:20vh;'>Task finished! Thanks for the participation! 😎</h1>",
        unsafe_allow_html=True,
    )
    st.stop()


# --- Current image data ---
current = metadata[st.session_state.current_index]
image_id = current["image_id"]
existing_ann = st.session_state.annotations.get(image_id)

# Pre-fill if revisiting
if existing_ann and st.session_state.selected_age is None:
    st.session_state.selected_age = existing_ann["age"]
    st.session_state.uncertain = existing_ann["uncertain"]


# --- Layout ---
left_col, right_col = st.columns([65, 35])

# --- Left: Image ---
with left_col:
    # Navigation bar
    nav_cols = st.columns([1, 3, 1])
    with nav_cols[0]:
        st.button("← Prev", on_click=go_prev, disabled=st.session_state.current_index == 0)
    with nav_cols[1]:
        status = "✓" if existing_ann else ""
        st.markdown(
            f"<h3 style='text-align:center;margin:0;'>Image {st.session_state.current_index + 1} / {total_images} {status}</h3>",
            unsafe_allow_html=True,
        )
    with nav_cols[2]:
        st.button("Next →", on_click=go_next, disabled=st.session_state.current_index == total_images - 1)

    # Load and display image
    raw_image = load_image(HF_REPO_ID, HF_TOKEN, image_id)

    brightness = st.slider("Brightness", -50, 50, key="brightness")
    contrast = st.slider("Contrast", -50, 50, key="contrast")

    if brightness != 0 or contrast != 0:
        display_image = adjust_image(raw_image, brightness, contrast)
    else:
        display_image = raw_image

    img_btn_cols = st.columns(2)
    with img_btn_cols[0]:
        clahe_on = st.toggle("CLAHE enhance", key="clahe_on")
    with img_btn_cols[1]:
        def _reset_image():
            st.session_state.brightness = 0
            st.session_state.contrast = 0
            st.session_state.clahe_on = False
        st.button("Reset image", on_click=_reset_image)

    if clahe_on:
        display_image = clahe_enhancement(display_image)

    st.image(display_image, use_container_width=True)

# --- Right: Controls ---
with right_col:
    # Metadata
    st.subheader("Metadata")
    st.write(f"**Length:** {current.get('length', 'N/A')}")
    st.write(f"**Month:** {current.get('month', 'N/A')}")

    # Map
    lat = current.get("latitude")
    lon = current.get("longitude")
    if lat and lon:
        lat, lon = float(lat), float(lon)
        m = folium.Map(location=[lat, lon], zoom_start=6, width=300, height=200)
        folium.Marker([lat, lon]).add_to(m)
        st_folium(m, width=300, height=200)

    # Age buttons
    st.subheader("Age")
    age_cols = st.columns(5)
    for i in range(1, 21):
        col = age_cols[(i - 1) % 5]
        with col:
            is_selected = st.session_state.selected_age == i
            button_type = "primary" if is_selected else "secondary"
            if st.button(str(i), key=f"age_{i}", use_container_width=True, type=button_type):
                st.session_state.selected_age = i
                st.rerun()

    # Uncertain flag
    st.checkbox("Flag as uncertain", key="uncertain")

    # Submit
    can_submit = st.session_state.selected_age is not None
    if st.button("Submit", type="primary", disabled=not can_submit, use_container_width=True):
        save_annotation(
            worksheet=worksheet,
            image_id=image_id,
            annotator=annotator,
            age=st.session_state.selected_age,
            previous_age=int(float(current.get("previous_age", 0))),
            uncertain=st.session_state.uncertain,
            is_issue=str(current.get("is_issue", "")).upper() == "TRUE",
            existing_row=existing_ann["row_number"] if existing_ann else None,
        )
        # Update local cache instead of re-fetching the whole sheet
        st.session_state.annotations[image_id] = {
            "row_number": existing_ann["row_number"] if existing_ann else len(st.session_state.annotations) + 2,
            "annotator": annotator,
            "age": st.session_state.selected_age,
            "previous_age": int(float(current.get("previous_age", 0))),
            "uncertain": st.session_state.uncertain,
        }
        # Auto-advance: set index and flag to load annotation on next rerun
        if st.session_state.current_index < total_images - 1:
            st.session_state.current_index += 1
            st.session_state._needs_annotation_load = True
        st.rerun()

    # Progress bar
    annotated_count = len(st.session_state.annotations)
    st.progress(annotated_count / total_images)
    st.caption(f"{annotated_count} / {total_images} annotated")


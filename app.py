import streamlit as st
import pandas as pd
from gpt_medical_info_extractor import get_processed_notes, extract_info_from_notes
from clinical_note import process_structured_info
import time  # To measure processing time
import json  # To enable downloading processed notes as JSON

# Set up the Streamlit page configuration
st.set_page_config(
    page_title="Clinical Notes Visualizer",  # Title for the browser tab
    layout="wide",  # Use the wide layout for better visualization
)

# Display the main title of the app
st.title("Clinical Notes Visualizer")

# Add a description of the app's functionality
st.markdown("""
This app is designed to process and visualize custom clinical notes. 
You can enter your own clinical note in the sidebar and process it using GPT.
Example notes are provided for testing purposes only.
""")

# Sidebar setup for user input and settings
with st.sidebar:
    st.header("Settings")  # Header for the settings section
    
    # Allows user to input their OpenAI API key
    api_key = st.text_input(
        "Enter your OpenAI API Key", 
        type="password", 
        help="Required to process notes."  # Tooltip for the input field
    )
    
    # Text area for entering custom clinical notes
    custom_note = st.text_area(
        "Enter your own clinical note", 
        height=300, 
        help="Paste your clinical note here."
    )
    
    # Option to load example notes for testing
    load_examples = st.checkbox(
        "Load example notes (for testing only)", 
        value=False
    )
    
    # Number input for selecting the number of example notes to load
    num_examples = st.number_input(
        "Number of example notes", 
        min_value=1, 
        max_value=10, 
        value=2, 
        disabled=not load_examples  # Disabled if `load_examples` is not checked
    )
    
    # Footer in the sidebar
    st.markdown("---")
    st.write("Created with Streamlit and OpenAI GPT")

# Function to display a section of the clinical note
def display_section(title, content):
    """
    Display a section of the note with appropriate formatting.
    Args:
        title (str): Section title to display.
        content (str/dict/list): Content of the section.
    """
    st.subheader(title)  # Display section title
    if isinstance(content, dict):  # If the content is a dictionary, format key-value pairs
        for key, value in content.items():
            st.write(f"**{key.capitalize()}:** {value}")
    elif isinstance(content, (list, str)):  # Handle lists and strings
        st.write(content if isinstance(content, str) else "\n".join(f"- {item}" for item in content))
    else:  # Default case if content is not available
        st.info("No information available.")

# Function to display a single processed note
def display_note(note, index):
    """
    Display the processed note's details section by section.
    Args:
        note (dict): Processed note data.
        index (int): Note index for display purposes.
    """
    st.header(f"Note {index}")  # Header for the note
    
    # List of sections to display with their keys
    sections = [
        ("Patient Demographics", "patient_demographics"),
        ("Chief Complaint", "chief_complaint"),
        ("History of Present Illness", "history_of_present_illness"),
        ("Clinical Findings", "clinical_findings"),
        ("Imaging Findings", "imaging_findings"),
        ("Laboratory Results", "laboratory_results"),
        ("Diagnosis", "diagnosis"),
        ("Treatment Plan", "treatment_plan"),
        ("Outcome", "outcome")
    ]
    
    # Display each section using the `display_section` function
    for title, key in sections:
        display_section(title, note.get(key, "No information available."))
    
    st.markdown("---")  # Add a horizontal divider

# Load example notes if requested
if load_examples:
    try:
        # Attempt to load example notes using the specified number
        example_notes = get_processed_notes(num_examples, api_key, process=False)
    except Exception as e:
        # Display an error message if loading fails
        st.error(f"Failed to load example notes: {str(e)}")
        example_notes = []
else:
    example_notes = []

# Combine custom note and example notes into a single list
all_notes = [custom_note.strip()] if custom_note.strip() else []
all_notes.extend(example_notes)

# Display a warning if no notes are available
if not all_notes:
    st.warning("Please enter a custom note in the sidebar or load example notes for testing.")
else:
    # Create a dropdown menu for selecting a note to preview
    note_options = ["Custom Note"] if custom_note else []
    note_options.extend([f"Example Note {i+1}" for i in range(len(example_notes))])
    selected_note_index = st.selectbox(
        "Select a note to preview", 
        range(len(all_notes)), 
        format_func=lambda x: note_options[x]
    )

    # Display the selected note in a text area for review
    st.subheader("Selected Note Preview")
    st.text_area("", value=all_notes[selected_note_index], height=300, disabled=True)

    # Process the selected note when the button is clicked
    if st.button("Process Selected Note"):
        if not api_key.strip():  # Check if API key is missing
            st.error("Please enter your OpenAI API Key")
        else:
            # Start timing the processing
            start_time = time.time()
            
            with st.spinner("Processing note..."):  # Show a spinner during processing
                try:
                    # Process the selected note using the provided API key
                    processed_note = extract_info_from_notes(all_notes[selected_note_index], api_key)
                    
                    # Display the processed note details
                    display_note(processed_note, selected_note_index + 1)
                except Exception as e:
                    # Display an error message if processing fails
                    st.error(f"An error occurred: {str(e)}")
            
            # Calculate and display the processing time
            elapsed_time = time.time() - start_time
            st.success(f"Note processed in {elapsed_time:.2f} seconds.")

            # Prepare and provide a download button for the processed note
            json_data = json.dumps(processed_note, indent=4)  # Convert note to JSON
            st.download_button(
                "Download Processed Note", 
                data=json_data, 
                file_name="processed_note.json", 
                mime="application/json"
            )
import os
import streamlit as st
import base64
import json
from pydantic import BaseModel, ValidationError, Field
from typing import Literal
from typing import List
from openai import OpenAI
import instructor


# ------------------- Pydantic model ------------------- #
class BookListing(BaseModel):
    book_title: str
    book_description: str
    book_condition: Literal["like New", "Excellent", "Good", "Fair"]

# ------------------- Page Configuration ------------------- #
st.set_page_config(page_title="Used Book Lister", layout="centered")
#client = instructor.patch(OpenAI())

# Initialize OpenAI API key from secrets
testy = os.environ["OPENAI_API_KEY"]


# Initialize instructor client
client = instructor.patch(OpenAI(api_key = testy))


# ------------------- Utility Functions ------------------- #
def encode_image_to_base64(file_bytes: bytes) -> str:
    """
    Encodes binary image data to a base64 string.
    """
    return base64.b64encode(file_bytes).decode("utf-8")

def call_gpt4_for_book_details(front_image_b64: str, back_image_b64: str) -> BookListing:
   """Uses GPT-4 with instructor to analyze book cover images and return structured book listing data."""
   try:
       response = client.chat.completions.create(
           model="gpt-4o",
           temperature=0.0,
           response_model=BookListing,
           messages=[
               {
                   "role": "system",
                   "content": "You are an assistant that analyzes book cover images to create attractive listings. Extract the title, create a selling description, and assess the condition.",
               },
               {
                   "role": "user",
                   "content": [
                       {
                           "type": "image_url",
                           "image_url": {"url": f"data:image/png;base64,{front_image_b64}"},
                       },
                       {
                           "type": "image_url",
                           "image_url": {"url": f"data:image/png;base64,{back_image_b64}"},
                       },
                   ],
               },
           ],
       )
       return response
   except Exception as e:
       raise ValueError(f"Failed to process the images or validate the output: {e}")


def reset_state():
    """
    Resets the page state to allow for a fresh upload.
    """
    st.session_state.page_state = "input_form"
    st.session_state.book_listing = None
    # To reset the file_uploader widgets, we can use Streamlit's experimental functionality
    # or rerun the script without manipulating the uploader keys directly.

# ------------------- Session State Initialization ------------------- #
if "page_state" not in st.session_state:
    st.session_state.page_state = "input_form"

if "book_listing" not in st.session_state:
    st.session_state.book_listing = None

# ------------------- Main App Logic ------------------- #
def main():
    st.title(f"Used Book Listing Creator")

    if st.session_state.page_state == "input_form":
        # -------------- Step 1: Image Uploads -------------- #
        front_cover = st.file_uploader("Front of Book", type=["png", "jpg", "jpeg"], key="front_cover")
        back_cover = st.file_uploader("Back of Book", type=["png", "jpg", "jpeg"], key="back_cover")

        # -------------- Submit Button -------------- #
        if st.button("SUBMIT"):
            if not front_cover or not back_cover:
                st.warning("Please upload both the front and back cover images before submitting.")
                return

            # -------------- Call GPT-4 -------------- #
            with st.spinner("Processing images, please wait..."):
                front_b64 = encode_image_to_base64(front_cover.read())
                back_b64 = encode_image_to_base64(back_cover.read())

                try:
                    book_listing = call_gpt4_for_book_details(front_b64, back_b64)
                    # Store the result and switch page state
                    st.session_state.book_listing = book_listing
                    st.session_state.page_state = "results"
                    st.rerun()
                except ValueError as e:
                    st.error(f"Error: {e}")

    elif st.session_state.page_state == "results":
        # -------------- Display Results -------------- #
        book_listing = st.session_state.book_listing
        if book_listing:
            st.header("TITLE:")
            st.write(book_listing.book_title)

            st.header("DESCRIPTION:")
            st.write(book_listing.book_description)

            st.header("CONDITION ESTIMATE:")
            st.write(book_listing.book_condition)

        # -------------- Next Book -------------- #
        if st.button("Next Book"):
            reset_state()
            st.rerun()

if __name__ == "__main__":
    main()

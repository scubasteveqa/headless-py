import os
import time
import base64
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io

st.set_page_config(page_title="Headless Chrome Browser Automation", layout="wide")
st.title("🌐 Web Automation with Headless Chrome")

class HeadlessBrowser:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        
    def start_browser(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), 
                                        options=self.options)
        return self.driver
        
    def take_screenshot(self, url):
        driver = self.start_browser()
        try:
            driver.get(url)
            time.sleep(2)  # Wait for page to fully load
            screenshot = driver.get_screenshot_as_png()
            return screenshot
        finally:
            driver.quit()
            
    def extract_text(self, url, css_selector):
        driver = self.start_browser()
        try:
            driver.get(url)
            elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
            )
            results = [element.text for element in elements]
            return results
        finally:
            driver.quit()
            
    def generate_pdf(self, url):
        driver = self.start_browser()
        try:
            driver.get(url)
            time.sleep(2)  # Wait for page to fully load
            
            # Generate PDF using Chrome's DevTools Protocol
            pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,
                "paperWidth": 8.5,
                "paperHeight": 11,
                "marginTop": 0.4,
                "marginBottom": 0.4,
                "marginLeft": 0.4,
                "marginRight": 0.4
            })
            
            return base64.b64decode(pdf_data['data'])
        finally:
            driver.quit()

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Sidebar for input fields
with st.sidebar:
    st.header("Input Parameters")
    url = st.text_input("Enter URL:", value="https://www.python.org")
    
    operation = st.radio(
        "Select Operation:",
        ["Screenshot", "Extract Text", "Generate PDF"]
    )
    
    if operation == "Extract Text":
        css_selector = st.text_input("CSS Selector:", value="h2, p")

# Initialize browser instance
browser = HeadlessBrowser()

# Main content area
if st.button("Run Operation", type="primary"):
    with st.spinner("Processing..."):
        if operation == "Screenshot":
            st.subheader("Screenshot")
            screenshot = browser.take_screenshot(url)
            
            # Display screenshot
            image = Image.open(io.BytesIO(screenshot))
            st.image(image, caption=f"Screenshot of {url}", use_column_width=True)
            
            # Add download button
            st.download_button(
                label="Download Screenshot",
                data=screenshot,
                file_name="screenshot.png",
                mime="image/png"
            )
            
        elif operation == "Extract Text":
            st.subheader("Extracted Text")
            try:
                results = browser.extract_text(url, css_selector)
                
                if not results:
                    st.warning(f"No elements found matching selector: '{css_selector}'")
                else:
                    for i, text in enumerate(results):
                        if text.strip():  # Only display non-empty text
                            st.write(f"Element {i+1}:")
                            st.info(text)
            except Exception as e:
                st.error(f"Error extracting text: {str(e)}")
                
        elif operation == "Generate PDF":
            st.subheader("Generated PDF")
            try:
                pdf_data = browser.generate_pdf(url)
                
                # Provide download button
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name="webpage.pdf",
                    mime="application/pdf"
                )
                
                # Display PDF preview (using iframe)
                base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")

st.divider()
st.markdown("""
### Instructions
1. Enter a URL in the sidebar
2. Choose an operation (Screenshot, Extract Text, or Generate PDF)
3. For text extraction, specify the CSS selector
4. Click "Run Operation" to execute
""")

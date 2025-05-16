from shiny import App, ui, render, reactive
import matplotlib.pyplot as plt
import io
import base64
import tempfile
import os
import sys
import time
from PIL import Image

# Import selenium for controlling headless Chrome
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# UI definition with sidebar layout
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h3("Website Screenshot Tool"),
        ui.input_text("url", "Enter URL:", value="https://www.python.org/"),
        ui.input_slider("width", "Viewport Width:", min=320, max=1920, value=1280, step=10),
        ui.input_slider("height", "Viewport Height:", min=320, max=1080, value=800, step=10),
        ui.input_checkbox("full_page", "Capture Full Page", value=False),
        ui.hr(),
        ui.input_action_button("capture", "Capture Screenshot", class_="btn-primary"),
        ui.download_button("download", "Download Screenshot"),
        ui.hr(),
        ui.p("This app uses headless Chrome via Selenium to capture website screenshots."),
    ),
    ui.card(
        ui.card_header("Screenshot Preview"),
        ui.output_ui("status_message"),
        ui.output_image("screenshot_output"),
        full_screen=True
    ),
    title="Headless Chrome Screenshot Tool",
)

def server(input, output, session):
    # Store the captured screenshot and status
    screenshot_data = reactive.value(None)
    driver = reactive.value(None)
    
    # Initialize the headless Chrome browser
    @reactive.effect
    def initialize_chrome():
        try:
            # Set up Chrome options for headless mode
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Initialize the browser
            driver_instance = webdriver.Chrome(options=chrome_options)
            driver(driver_instance)
            ui.notification_show("Headless Chrome initialized successfully", type="message")
        except Exception as e:
            ui.notification_show(f"Failed to initialize Chrome: {str(e)}", type="error")
    
    # Clean up Chrome when the app is closed
    @reactive.effect
    def cleanup_on_exit():
        session.on_ended(lambda: close_chrome())
    
    def close_chrome():
        if driver() is not None:
            try:
                driver().quit()
            except:
                pass
    
    # Status message display
    @render.ui
    def status_message():
        if driver() is None:
            return ui.div(
                ui.tags.div(
                    ui.tags.i(class_="fa fa-exclamation-triangle"), 
                    " Chrome not available. Please wait for initialization or check console for errors.",
                    class_="alert alert-warning"
                )
            )
        elif screenshot_data() is None:
            return ui.div(
                ui.tags.div(
                    ui.tags.i(class_="fa fa-info-circle"),
                    " Click 'Capture Screenshot' to take a screenshot.",
                    class_="alert alert-info"
                )
            )
        return None
    
    # Capture screenshot when the button is clicked
    @reactive.effect
    @reactive.event(input.capture)
    def take_screenshot():
        if driver() is None:
            ui.notification_show("Chrome is not initialized yet", type="error")
            return
        
        # Check if URL is valid
        url = input.url()
        if not url:
            ui.notification_show("Please enter a valid URL", type="warning")
            return
        
        # Add http:// if missing
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        
        with ui.Progress(min=0, max=100) as p:
            p.set(message="Taking screenshot...", detail="Navigating to page", value=0)
            
            try:
                # Navigate to the URL
                driver().get(url)
                p.set(value=30, detail="Page loaded")
                
                # Set viewport size
                driver().set_window_size(input.width(), input.height())
                p.set(value=50, detail="Setting viewport size")
                
                # Wait for page to load completely
                time.sleep(2)  # Simple wait for page load
                p.set(value=70, detail="Waiting for page to load")
                
                # Take screenshot
                if input.full_page():
                    # Get page dimensions and scroll through
                    p.set(value=80, detail="Taking full page screenshot")
                    
                    # Get the height of the entire page
                    total_height = driver().execute_script("return document.body.scrollHeight")
                    driver().set_window_size(input.width(), total_height)
                    
                    # Take screenshot after resize
                    time.sleep(0.5)
                    
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                driver().save_screenshot(temp_file.name)
                
                # Read the image into memory
                with open(temp_file.name, "rb") as file:
                    img_data = file.read()
                
                # Store the screenshot data
                screenshot_data(img_data)
                os.unlink(temp_file.name)  # Delete the temp file
                
                p.set(value=100, detail="Screenshot captured")
                ui.notification_show("Screenshot captured successfully", type="message")
                
            except Exception as e:
                ui.notification_show(f"Error capturing screenshot: {str(e)}", type="error")
    
    # Display the screenshot - Fixed to avoid data URL issue
    @render.image
    def screenshot_output():
        # If no screenshot, return a blank/transparent image
        if screenshot_data() is None:
            blank_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            buffer = io.BytesIO()
            blank_img.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer
        
        # Return the actual screenshot
        return io.BytesIO(screenshot_data())
    
    # Handle downloads
    @session.download(filename=lambda: f"screenshot-{time.strftime('%Y%m%d-%H%M%S')}.png")
    def download():
        if screenshot_data() is None:
            return None
        return io.BytesIO(screenshot_data())

app = App(app_ui, server)

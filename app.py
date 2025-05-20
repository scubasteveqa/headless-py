from shiny import App, reactive, render, ui
import base64
import io
from chromote import Chromote

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_text("url", "Website URL", value="https://www.example.com"),
        ui.input_numeric("width", "Screenshot Width (pixels)", value=1024, min=320, max=1920),
        ui.input_numeric("height", "Screenshot Height (pixels)", value=768, min=240, max=1080),
        ui.input_action_button("capture", "Capture Screenshot"),
    ),
    ui.card(
        ui.card_header("Screenshot Preview"),
        ui.output_ui("screenshot"),
    ),
)

def server(input, output, session):
    chrome = reactive.value(None)
    
    @reactive.effect
    def _():
        # Initialize chromote when the app starts
        nonlocal chrome
        chrome_instance = Chromote()
        chrome.set(chrome_instance)
    
    @render.ui
    @reactive.event(input.capture)
    def screenshot():
        if chrome.get() is None:
            return ui.p("Chrome is still initializing...")
        
        try:
            # Get a new tab in Chrome
            tab = chrome.get().new_tab()
            
            # Navigate to the URL
            tab.goto(input.url())
            
            # Set viewport size
            tab.set_viewport(width=input.width(), height=input.height())
            
            # Wait for page to load
            tab.wait_until("load")
            
            # Capture screenshot
            screenshot_data = tab.screenshot()
            
            # Close the tab when done
            tab.close()
            
            # Convert the binary data to base64 for display
            base64_data = base64.b64encode(screenshot_data).decode("utf-8")
            
            return ui.img(
                src=f"data:image/png;base64,{base64_data}",
                style="max-width: 100%; border: 1px solid #ddd;"
            )
        except Exception as e:
            return ui.div(
                ui.h4("Error capturing screenshot:"),
                ui.p(str(e)),
                style="color: red;"
            )

app = App(app_ui, server)

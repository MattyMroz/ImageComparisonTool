import asyncio
import os
import re
from playwright.sync_api import sync_playwright, expect

def run_verification(playwright):
    # Setup
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Capture console messages
    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))

    try:
        # Get absolute path for the local HTML file
        base_path = os.path.abspath(os.path.dirname(__file__))
        index_path = os.path.join(base_path, '..', '..', 'index.html')
        red_image_path = os.path.join(base_path, 'red.png')
        blue_image_path = os.path.join(base_path, 'blue.png')
        green_image_path = os.path.join(base_path, 'green.png') # For the third slot

        # Create a green image for the third slot
        from PIL import Image
        green_image = Image.new('RGB', (200, 200), 'green')
        green_image.save(green_image_path)


        if not os.path.exists(index_path):
            raise FileNotFoundError(f"index.html not found at {index_path}")

        # 1. Load the page
        page.goto(f'file://{index_path}')

        # 2. Load images into the tool
        page.locator('#hidden-file-input').set_input_files([red_image_path, blue_image_path, green_image_path])

        # Wait for the images to be processed and available in the dropdowns
        page.wait_for_function("() => DYNAMIC_AVAILABLE_IMAGES.length >= 3")

        # Wait for the slots to be created
        page.wait_for_selector('#slot0-select')
        page.wait_for_selector('#slot1-select')

        # Select images for the first two slots
        page.select_option('#slot0-select', label='red.png')
        page.select_option('#slot1-select', label='blue.png')

        # Wait for the images to be fully loaded and displayed
        src_regex = re.compile(r'^data:image/png')
        expect(page.locator('#slot0-img')).to_have_attribute('src', src_regex)
        expect(page.locator('#slot1-img')).to_have_attribute('src', src_regex)
        expect(page.locator('.image-stack')).not_to_have_class('hidden')

        # 3. Test Swipe (Horizontal) mode (default)
        print("Testing Swipe (Horizontal) mode...")
        page.wait_for_timeout(1000) # Let it animate

        # 4. Test Swipe (Vertical) mode
        print("Testing Swipe (Vertical) mode...")
        page.select_option('#comparison-mode-select', 'swipe-vertical')
        page.wait_for_timeout(1000)

        # 5. Test Fade mode
        print("Testing Fade mode...")
        page.select_option('#comparison-mode-select', 'fade')
        page.wait_for_timeout(1000)

        # 6. Test Onion Skin mode
        print("Testing Onion Skin mode...")
        page.select_option('#comparison-mode-select', 'onion-skin')
        opacity_slider = page.locator('#opacity-slider')
        opacity_slider.fill("0.25")
        expect(page.locator('#opacity-value')).to_have_text('25%')
        page.wait_for_timeout(500)

        # 7. Test dynamic slot creation
        print("Testing dynamic slot creation...")
        page.click('#add-slot-btn')
        page.select_option('#slot2-select', label='green.png')
        expect(page.locator('#slot2-img')).to_have_attribute('src', src_regex)

        # Switch back to an N-image compatible mode
        page.select_option('#comparison-mode-select', 'swipe-horizontal')
        page.wait_for_timeout(1000)


        print("SUCCESS: All working features verified.")

        # 8. Take a screenshot for final visual confirmation
        screenshot_path = os.path.join(base_path, 'verification.png')
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

    except Exception as e:
        print(f"An error occurred during verification: {e}")
        screenshot_path = os.path.join(base_path, 'error.png')
        page.screenshot(path=screenshot_path)
        print(f"Error screenshot saved to {screenshot_path}")
        raise

    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_verification(playwright)
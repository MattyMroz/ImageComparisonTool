import asyncio
import os
import re
from playwright.sync_api import sync_playwright, expect

def run_verification(playwright):
    # Setup
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Get absolute path for the local HTML file
        base_path = os.path.abspath(os.path.dirname(__file__))
        index_path = os.path.join(base_path, '..', '..', 'index.html')
        red_image_path = os.path.join(base_path, 'red.png')
        blue_image_path = os.path.join(base_path, 'blue.png')

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"index.html not found at {index_path}")
        if not os.path.exists(red_image_path):
            raise FileNotFoundError(f"red.png not found at {red_image_path}")
        if not os.path.exists(blue_image_path):
            raise FileNotFoundError(f"blue.png not found at {blue_image_path}")

        # 1. Load the page
        page.goto(f'file://{index_path}')

        # 2. Load images into the tool
        page.locator('#hidden-file-input').set_input_files([red_image_path, blue_image_path])

        # Wait for the images to be processed and available in the dropdowns
        page.wait_for_function("() => DYNAMIC_AVAILABLE_IMAGES.length >= 2")
        page.select_option('#slot0-select', label='red.png')
        # The second slot is slot 1 in the original code
        page.select_option('#slot1-select', label='blue.png')

        # Wait for the images to be fully loaded and displayed
        src_regex = re.compile(r'^data:image/png')
        expect(page.locator('#slot0-img')).to_have_attribute('src', src_regex)
        expect(page.locator('#slot1-img')).to_have_attribute('src', src_regex)
        expect(page.locator('.image-stack')).not_to_have_class('hidden')

        # 3. Switch to Manual Slider mode (assuming it exists in this version)
        # This part might fail if the feature wasn't in the original code
        if page.locator('#comparison-mode-select').is_visible():
            page.select_option('#comparison-mode-select', 'manual-slider')
            expect(page.locator('#manual-slider-handle')).not_to_have_class('hidden')
        else:
            print("Skipping manual slider mode selection, as control is not visible.")


        # 4. Zoom in to create a more complex test case
        main_view = page.locator('#main-view-area')
        main_view_bb = main_view.bounding_box()
        page.mouse.move(main_view_bb['x'] + main_view_bb['width'] / 2, main_view_bb['y'] + main_view_bb['height'] / 2)
        page.mouse.wheel(0, -200) # Zoom in
        page.wait_for_timeout(500)

        # 5. Drag the slider
        handle = page.locator('#manual-slider-handle')
        handle.hover()
        page.mouse.down()

        drag_to_x = main_view_bb['x'] + main_view_bb['width'] * 0.75
        drag_to_y = main_view_bb['y'] + main_view_bb['height'] / 2

        page.mouse.move(drag_to_x, drag_to_y)
        page.mouse.up()

        page.wait_for_timeout(500)

        # 6. Capture the state
        handle_bb_after = handle.bounding_box()
        clipper_width_str = page.locator('#slot1-clipper').evaluate("el => el.style.width")

        # 7. Mathematical Verification
        handle_position_percent = ((handle_bb_after['x'] + handle_bb_after['width'] / 2) - main_view_bb['x']) / main_view_bb['width']
        clipper_width_percent = float(clipper_width_str.replace('%', '')) / 100

        print(f"Verification - Handle Position: {handle_position_percent:.4f}, Clipper Width: {clipper_width_percent:.4f}")

        assert abs(handle_position_percent - clipper_width_percent) < 0.02, \
            f"Synchronization failed! Handle at {handle_position_percent:.4f} but clipper at {clipper_width_percent:.4f}"

        print("SUCCESS: Manual slider handle and clipper are correctly synchronized after zoom and drag.")

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
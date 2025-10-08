import asyncio
from playwright.async_api import async_playwright, expect
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Get the absolute path to the index.html file
        html_file_path = os.path.abspath('index.html')

        await page.goto(f'file://{html_file_path}')

        # Wait for the file input to be attached
        await page.wait_for_selector('#hidden-file-input', state='attached')

        # Provide paths to the SVG files
        red_svg_path = os.path.abspath('jules-scratch/verification/red.svg')
        green_svg_path = os.path.abspath('jules-scratch/verification/green.svg')
        blue_svg_path = os.path.abspath('jules-scratch/verification/blue.svg')

        # Load two images first to test the manual slider
        await page.locator('#hidden-file-input').set_input_files([red_svg_path, green_svg_path])
        await page.wait_for_timeout(500)

        # Wait for options to be populated
        await page.wait_for_selector('#slot0-select option:nth-child(2)', state='attached')

        # Select images
        await page.select_option('#slot0-select', index=1)
        await page.select_option('#slot1-select', index=2)
        await page.wait_for_timeout(200)

        # --- Test 1: Manual Slider (Horizontal) Fix ---
        await page.select_option('#comparison-mode-select', 'manual-slider')
        await page.wait_for_selector('#manual-slider-controls', state='visible')
        await page.select_option('#manual-slider-direction', 'horizontal')
        await page.wait_for_timeout(200)

        handle = page.locator('#manual-slider-handle')
        main_view_area = page.locator('#main-view-area')

        # Get bounding boxes for accurate dragging relative to the viewport
        handle_bb = await handle.bounding_box()
        view_area_bb = await main_view_area.bounding_box()

        if handle_bb and view_area_bb:
            # Start drag from the center of the handle
            start_x = handle_bb['x'] + handle_bb['width'] / 2
            start_y = handle_bb['y'] + handle_bb['height'] / 2

            # Drag to 25% of the main view area width
            target_x = view_area_bb['x'] + view_area_bb['width'] * 0.25

            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            await page.mouse.move(target_x, start_y)
            await page.mouse.up()

        await page.wait_for_timeout(500)
        await page.screenshot(path='jules-scratch/verification/final_slider_fix.png')

        # --- Test 2: Control Panel Horizontal Scroll & Mode Disabling ---
        await page.locator('#hidden-file-input').set_input_files([blue_svg_path])
        await page.click('#add-slot-btn')
        await page.wait_for_selector('#slot2-select')
        await page.wait_for_timeout(200)
        await page.select_option('#slot2-select', index=3)
        await page.wait_for_timeout(200)

        # Add more slots to force scroll
        for i in range(8):
            await page.click('#add-slot-btn')
            await page.wait_for_selector(f'#slot{i+3}-select')

        # Check that 2-image modes are disabled
        onion_skin_option = page.locator('select#comparison-mode-select option[value="onion-skin"]')
        manual_slider_option = page.locator('select#comparison-mode-select option[value="manual-slider"]')
        await expect(onion_skin_option).to_be_disabled()
        await expect(manual_slider_option).to_be_disabled()

        # Scroll the controls to the right and take a screenshot
        await page.evaluate("document.getElementById('controls').scrollLeft = 500")
        await page.wait_for_timeout(500)
        await page.screenshot(path='jules-scratch/verification/final_controls_fix.png')


        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
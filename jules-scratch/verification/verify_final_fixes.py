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

        # Load images
        await page.locator('#hidden-file-input').set_input_files([red_svg_path, green_svg_path])
        await page.wait_for_timeout(500) # Allow DOM to update

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
        image_stack = page.locator('.image-stack')

        # Get bounding boxes for accurate dragging
        handle_bb = await handle.bounding_box()
        image_stack_bb = await image_stack.bounding_box()

        if handle_bb and image_stack_bb:
            # Start drag from the center of the handle
            start_x = handle_bb['x'] + handle_bb['width'] / 2
            start_y = handle_bb['y'] + handle_bb['height'] / 2

            # Drag to 25% of the image stack width
            target_x = image_stack_bb['x'] + image_stack_bb['width'] * 0.25

            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            await page.mouse.move(target_x, start_y)
            await page.mouse.up()

        await page.wait_for_timeout(500)
        await page.screenshot(path='jules-scratch/verification/final_manual_slider.png')

        # --- Test 2: Control Panel Horizontal Scroll ---
        # Add enough slots to force a scroll
        for i in range(8):
            await page.click('#add-slot-btn')
            await page.wait_for_selector(f'#slot{i+2}-select')

        # Scroll the controls to the right
        await page.evaluate("document.getElementById('controls').scrollLeft = 500")
        await page.wait_for_timeout(500)
        await page.screenshot(path='jules-scratch/verification/final_responsive_controls.png')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
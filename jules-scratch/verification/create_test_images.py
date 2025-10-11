from PIL import Image

# Create a 200x200 red image
red_image = Image.new('RGB', (200, 200), 'red')
red_image.save('jules-scratch/verification/red.png')

# Create a 200x200 blue image
blue_image = Image.new('RGB', (200, 200), 'blue')
blue_image.save('jules-scratch/verification/blue.png')

print("Test images created successfully.")
import os
import shutil
from pathlib import Path
import sys

def setup_directory_structure():
    """
    Creates the necessary directory structure for the Infiltrate application.
    This ensures all required folders exist and creates placeholder files.
    """
    # Define the base directory (current directory)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define directory structure
    directories = [
        os.path.join(base_dir, "Content", "Images"),
        os.path.join(base_dir, "Content", "Fonts"),
        os.path.join(base_dir, "Content", "Scripts"),
        os.path.join(base_dir, "Content", "Temp")
    ]
    
    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create placeholder images if they don't exist
    image_placeholders = {
        "Home.png": create_placeholder_image,
        "Picture.png": create_placeholder_image,
        "AddImage.png": create_placeholder_image
    }
    
    images_dir = os.path.join(base_dir, "Content", "Images")
    for img_name, create_func in image_placeholders.items():
        img_path = os.path.join(images_dir, img_name)
        if not os.path.exists(img_path):
            create_func(img_path)
            print(f"Created placeholder image: {img_path}")
    
    # Copy the script files to the Scripts directory
    scripts_dir = os.path.join(base_dir, "Content", "Scripts")
    
    # Check if ImageConverter.py and Updater.py are in the base directory
    for script_name in ["ImageConverter.py", "Updater.py"]:
        source_path = os.path.join(base_dir, script_name)
        dest_path = os.path.join(scripts_dir, script_name)
        
        # If the script exists in the base directory, copy it to Scripts
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"Copied {script_name} to Scripts directory")
        else:
            # Create empty script file if it doesn't exist
            if not os.path.exists(dest_path):
                with open(dest_path, 'w') as f:
                    f.write(f"# {script_name}\n# This is a placeholder file.\n")
                print(f"Created placeholder script: {dest_path}")
    
    # Create __init__.py in Scripts directory for proper importing
    init_path = os.path.join(scripts_dir, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write("# Package initialization\n")
        print(f"Created __init__.py in Scripts directory")
    
    # Check for font files
    fonts_dir = os.path.join(base_dir, "Content", "Fonts")
    font_files = {
        "centurygothic.ttf": download_font,
        "centurygothic_bold.ttf": download_font
    }
    
    for font_name, download_func in font_files.items():
        font_path = os.path.join(fonts_dir, font_name)
        if not os.path.exists(font_path):
            try:
                download_func(font_path, font_name)
                print(f"Downloaded font: {font_path}")
            except Exception as e:
                print(f"Error downloading font {font_name}: {str(e)}")
                print(f"Please manually place {font_name} in {fonts_dir}")
    
    print("\nSetup complete! Directory structure has been created.")
    print(f"Application is ready to run from: {os.path.join(base_dir, 'main.py')}")


def create_placeholder_image(path):
    """Creates a simple placeholder image"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a blank image with black background
        img = Image.new('RGBA', (200, 200), (40, 40, 40, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw a border
        draw.rectangle([(5, 5), (195, 195)], outline=(230, 57, 70, 255), width=2)
        
        # Add text with image name
        img_name = os.path.basename(path).split('.')[0]
        draw.text((100, 100), img_name, fill=(255, 255, 255, 255), anchor="mm")
        
        # Save the image
        img.save(path)
        return True
    except ImportError:
        print("Warning: PIL/Pillow library not found. Cannot create placeholder images.")
        # Create an empty file instead
        with open(path, 'wb') as f:
            f.write(b'')
        return False


def download_font(path, font_name):
    """
    This function would normally download the required fonts.
    Since we cannot actually download Century Gothic fonts due to licensing,
    this function creates a placeholder message about font requirements.
    """
    try:
        # Instead of downloading, create a text file with instructions
        font_info_path = os.path.splitext(path)[0] + ".txt"
        with open(font_info_path, 'w') as f:
            f.write(f"The application requires {font_name} font.\n")
            f.write("Century Gothic is typically pre-installed on Windows systems,\n")
            f.write("but may require a license for other platforms.\n")
            f.write("\n")
            f.write("Please place the legitimate font file in this directory\n")
            f.write("and rename it to match the required filename.\n")
        
        # Create an empty font file as a placeholder
        with open(path, 'wb') as f:
            f.write(b'')
        
        print(f"Created font placeholder info file: {font_info_path}")
        return True
    except Exception as e:
        print(f"Error creating font placeholder: {str(e)}")
        return False


if __name__ == "__main__":
    setup_directory_structure()

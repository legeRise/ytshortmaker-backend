from PIL import Image, ImageDraw, ImageFont,ImageStat,ImageFilter,ImageEnhance
from django.conf import settings
import os

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = current_line + " " + word
        if draw.textlength(test_line, font) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines

def draw_text_centered(draw, lines, position, font, max_width, padding, fill='yellow'):
    y = position[1]

    for line in lines:
        text_width = draw.textlength(line, font)
        x = position[0] + (max_width - text_width) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += font.getsize('hg')[1] + padding

def get_wrapped_text_size(draw, lines, font, padding):
    line_height = font.getsize('hg')[1]
    total_height = len(lines) * (line_height + padding) - padding
    max_line_width = max(draw.textlength(line, font) for line in lines)
    return total_height, max_line_width

def dynamically_adjust_font(draw, text, font, max_width, max_height, padding):
    lines = wrap_text(draw, text, font, max_width)
    total_height, _ = get_wrapped_text_size(draw, lines, font, padding)
    while total_height > max_height and font.size > 10:
        font = ImageFont.truetype(font.path, font.size - 1)
        lines = wrap_text(draw, text, font, max_width)
        total_height, _ = get_wrapped_text_size(draw, lines, font, padding)
    return font, lines


def is_image_dark(image, dark_threshold=85, light_threshold=170):
    """Determine if the image is predominantly dark, light or in the middle and return a suitable color for overlay"""
    grayscale = image.convert('L')  # Convert to grayscale
    stat = ImageStat.Stat(grayscale)
    avg_brightness = stat.mean[0]

    if avg_brightness < dark_threshold:
        return ('dark','yellow')
    elif avg_brightness > light_threshold:
        return ('light','red')
    else:
        if avg_brightness < 128:
            return 'mid-dark', 'yellow' 
        else:
            return 'mid-light', 'red'  


def add_text_to_image(image_path, text, is_title=True, save_to=None):
    # Load the image
    image = Image.open(image_path)

    # Resize the image
    resized_image = image.resize((360, 740))

    # Get resized image dimensions
    image_width, image_height = resized_image.size

    # check if the image is more darker or more lighter
    image_brightness_level = is_image_dark(resized_image)

    # dark or light : edit accordingly to have text appear more clearly
    if image_brightness_level[0] == 'mid-dark':
        enhancer = ImageEnhance.Contrast(resized_image);
        resized_image = enhancer.enhance(0.75)
    elif image_brightness_level[0] == 'mid-light':
        enhancer = ImageEnhance.Contrast(resized_image);
        resized_image = enhancer.enhance(1.2)
        resized_image = resized_image.filter(ImageFilter.SMOOTH_MORE)
    else:
        resized_image = resized_image.filter(ImageFilter.DETAIL)

    # Create a drawing object
    draw = ImageDraw.Draw(resized_image)

    # setting up font_paths
    font_paths = {
        "black": os.path.join(settings.FONT_BASE_DIR,'Roboto-Black.ttf'),
        "bold": os.path.join(settings.FONT_BASE_DIR,'Roboto-Bold.ttf'),
        "medium": os.path.join(settings.FONT_BASE_DIR,'Roboto-Medium.ttf'),
        "light": os.path.join(settings.FONT_BASE_DIR,'Roboto-Light.ttf'),
        "thin": os.path.join(settings.FONT_BASE_DIR,'Roboto-Thin.ttf')
    }

    # Define fonts
    fonts = {
        "black": ImageFont.truetype(font_paths['black'], 40),
        "bold": ImageFont.truetype(font_paths['bold'], 35),
        "medium": ImageFont.truetype(font_paths['medium'], 40),
        "light": ImageFont.truetype(font_paths['light'], 30),
        "thin": ImageFont.truetype(font_paths['thin'], 30)
    }

    padding = 5
    margin_between = 50  # Margin between title and description
    safe_margin = 10  # Margin from the image edges

    if is_title:
        font = fonts["bold"]
        max_width = image_width - 2 * safe_margin
        max_height = (image_height - 2 * safe_margin) // 2

        # Dynamically adjust font size and wrap text
        font, lines = dynamically_adjust_font(draw, text, font, max_width, max_height, padding)

        # Calculate total text height
        total_height, _ = get_wrapped_text_size(draw, lines, font, padding)

        # Positioning
        if total_height > image_height - 2 * safe_margin:
            print("Text does not fit within the image boundaries.")
        else:
            position = (safe_margin, safe_margin + (image_height - total_height) // 2 - 120)

            # Draw the rectangle behind the text
            rect_x0 = safe_margin
            rect_x1 = image_width - safe_margin
            rect_y0 = position[1] - padding
            rect_y1 = rect_y0 + total_height + 2 * padding
            draw.rectangle([(rect_x0, rect_y0), (rect_x1, rect_y1)], fill="yellow")

            # Draw wrapped and centered text
            draw_text_centered(draw, lines, (safe_margin, rect_y0 + padding), font, rect_x1 - rect_x0, padding, fill='black')

    else:
        font = fonts["black"]
        max_width = image_width - 2 * safe_margin
        max_height = (image_height - 2 * safe_margin) // 2

        # Dynamically adjust font size and wrap text
        font, lines = dynamically_adjust_font(draw, text, font, max_width, max_height, padding)

        # Calculate total text height
        total_height, _ = get_wrapped_text_size(draw, lines, font, padding)

        # Positioning
        if total_height > image_height - 2 * safe_margin:
            print("Text does not fit within the image boundaries.")
        else:
            position = (safe_margin, safe_margin + (image_height - total_height) // 2)

            # Draw wrapped and centered text
            description_color =  image_brightness_level[1]
            draw_text_centered(draw, lines, position, font, max_width, padding,fill = description_color)

    # Save the image if save_to is provided
    if save_to:
        resized_image.save(save_to)

# Example usage:
if __name__ == '__main__':
    title_text = "Top 5 mountains in the world"
    description_text = "Mount Everest"

    add_text_to_image('test.png', title_text, is_title=True, save_to='output_title.png')
    add_text_to_image('test.png', description_text, is_title=False, save_to='output_description.png')

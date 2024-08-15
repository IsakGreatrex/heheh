import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to your pre-set PNG and font for text overlay
OVERLAY_IMAGE_PATH = "heheh2.png"
FONT_PATH = "impact.ttf"  # Path to a TTF font file on your system

# Start command handler
async def start(update: Update, context: CallbackContext) -> None:
    await show_options(update.message, context)

# Function to display the options to the user
async def show_options(message, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Center", callback_data='center')],
        [InlineKeyboardButton("Top Left", callback_data='top_left')],
        [InlineKeyboardButton("Bottom Right", callback_data='bottom_right')],
        [InlineKeyboardButton("Size 50%", callback_data='size_50')],
        [InlineKeyboardButton("Size 75%", callback_data='size_75')],
        [InlineKeyboardButton("Size 100%", callback_data='size_100')],
        [InlineKeyboardButton("Add Text Top", callback_data='text_top')],
        [InlineKeyboardButton("Add Text Bottom", callback_data='text_bottom')],
        [InlineKeyboardButton("Done", callback_data='done')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Choose overlay position, size, or add text. Click 'Done' when finished:", reply_markup=reply_markup)

# Callback query handler to process user selections
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'done':
        await query.edit_message_text(text="Thanks for using the bot! If you want to start over, type /start.")
        context.user_data.clear()  # Clear user data to reset selections
    elif "size" in data:
        size = int(data.split('_')[1])
        context.user_data['size'] = size
        await query.edit_message_text(text=f"Overlay size set to: {size}%. Now send me an image!")
    elif data == 'text_top':
        context.user_data['text_position'] = 'top'
        await query.edit_message_text(text="Please send me the text you want to add to the top.")
    elif data == 'text_bottom':
        context.user_data['text_position'] = 'bottom'
        await query.edit_message_text(text="Please send me the text you want to add to the bottom.")
    else:
        position = data
        context.user_data['position'] = position
        await query.edit_message_text(text=f"Overlay position set to: {position}. Now send me an image!")

# Text message handler to capture the text input
async def text_handler(update: Update, context: CallbackContext) -> None:
    text_position = context.user_data.get('text_position', None)
    if text_position:
        context.user_data[f'text_{text_position}'] = update.message.text
        await update.message.reply_text(f"Text for the {text_position} set. Now send me an image!")
        context.user_data.pop('text_position')  # Remove after setting

# Image handler to process the user's image
async def image_handler(update: Update, context: CallbackContext) -> None:
    # Get user-selected position, size, and text
    position = context.user_data.get('position', 'center')
    size = context.user_data.get('size', 100)
    text_top = context.user_data.get('text_top', '')
    text_bottom = context.user_data.get('text_bottom', '')

    # Check if the image is already stored in user_data
    if 'uploaded_image' in context.user_data:
        uploaded_image = context.user_data['uploaded_image']
    else:
        # Download the image
        photo = update.message.photo[-1]  # Get the best quality image
        photo_file = await photo.get_file()

        photo_bytes = BytesIO()
        await photo_file.download_to_memory(out=photo_bytes)
        photo_bytes.seek(0)

        uploaded_image = Image.open(photo_bytes).convert("RGBA")
        context.user_data['uploaded_image'] = uploaded_image  # Store the image

    overlay = Image.open(OVERLAY_IMAGE_PATH).convert("RGBA")

    # Scale overlay according to user selection
    new_size = (int(overlay.width * (size / 100)), int(overlay.height * (size / 100)))
    overlay = overlay.resize(new_size, Image.Resampling.LANCZOS)

    # Determine position and create combined image
    combined = Image.new('RGBA', uploaded_image.size)
    if position == 'top_left':
        combined.paste(overlay, (0, 0), overlay)
    elif position == 'bottom_right':
        combined.paste(overlay, (uploaded_image.width - overlay.width, uploaded_image.height - overlay.height), overlay)
    else:  # Center
        combined.paste(overlay, ((uploaded_image.width - overlay.width) // 2, (uploaded_image.height - overlay.height) // 2), overlay)
    
    combined = Image.alpha_composite(uploaded_image, combined)

    # Add text to the image if any
    draw = ImageDraw.Draw(combined)
    font = ImageFont.truetype(FONT_PATH, 40)  # Adjust font size as needed

    def draw_text_with_stroke(draw, position, text, font, stroke_width=2, stroke_fill="black", fill="white"):
        x, y = position
        # Draw the stroke by drawing the text in black slightly offset in all directions
        for offset in [(stroke_width, 0), (-stroke_width, 0), (0, stroke_width), (0, -stroke_width),
                       (stroke_width, stroke_width), (-stroke_width, -stroke_width),
                       (stroke_width, -stroke_width), (-stroke_width, stroke_width)]:
            draw.text((x + offset[0], y + offset[1]), text, font=font, fill=stroke_fill)
        # Draw the main text on top
        draw.text((x, y), text, font=font, fill=fill)

    # Top text
    if text_top:
        text_bbox = draw.textbbox((0, 0), text_top, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw_text_with_stroke(draw, ((combined.width - text_width) / 2, 10), text_top, font)

    # Bottom text
    if text_bottom:
        text_bbox = draw.textbbox((0, 0), text_bottom, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw_text_with_stroke(draw, ((combined.width - text_width) / 2, combined.height - text_height - 10), text_bottom, font)

    combined_bytes = BytesIO()
    combined.save(combined_bytes, format='PNG')
    combined_bytes.seek(0)

    await update.message.reply_photo(photo=InputFile(combined_bytes, filename="combined_image.png"))

    # Show the options again after processing the image, unless the user chose "Done"
    if 'done' not in context.user_data:
        await show_options(update.message, context)

def main() -> None:
    application = Application.builder().token("TOKENKEY").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(MessageHandler(filters.PHOTO, image_handler))

    application.run_polling()

if __name__ == '__main__':
    main()

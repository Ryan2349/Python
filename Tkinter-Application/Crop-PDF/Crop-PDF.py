import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageTk
from PIL import ImageOps
from pdf2image import convert_from_path

def load_pdf():
    """Load and display a one-page PDF file."""
    global pdf_image
    file_path = filedialog.askopenfilename(
        filetypes=[("PDF Files", "*.pdf")],
        title="Select a one-page PDF file"
    )
    if not file_path:
        return

    try:
        # Convert the PDF to images (one image per page)
        images = convert_from_path(file_path, dpi=200)

        # Check if the PDF has only one page
        if len(images) != 1:
            messagebox.showerror("Error", "Please upload a one-page PDF file.")
            return

        # Get the first (and only) page as an image
        pdf_image = images[0]

        # Display the image in the GUI
        display_image(pdf_image)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load PDF: {e}")

def display_image(image):
    """Display the given PIL image in the GUI."""
    global canvas, tk_image, scaled_image, image_scale, canvas_offset_x, canvas_offset_y
    canvas.delete("all")  # Clear previous image

    # Resize the image to fit the canvas (preserve aspect ratio)
    image_width, image_height = image.size
    canvas_width, canvas_height = 600, 800

    # Calculate scale factor and offsets to center the image
    scale_factor = min(canvas_width / image_width, canvas_height / image_height)
    new_width = int(image_width * scale_factor)
    new_height = int(image_height * scale_factor)
    scaled_image = image.resize((new_width, new_height))
    image_scale = scale_factor

    # Calculate offsets to center the image on the canvas
    canvas_offset_x = (canvas_width - new_width) // 2
    canvas_offset_y = (canvas_height - new_height) // 2

    # Convert the scaled image to a format suitable for tkinter
    tk_image = ImageTk.PhotoImage(scaled_image)
    canvas.create_image(canvas_offset_x, canvas_offset_y, anchor="nw", image=tk_image)

def start_crop(event):
    """Start the crop selection with mouse click."""
    global start_x, start_y, rect_id
    # Adjust for canvas offset
    start_x, start_y = event.x - canvas_offset_x, event.y - canvas_offset_y
    rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)

def update_crop(event):
    """Update the crop selection rectangle as the mouse is dragged."""
    global rect_id
    # Constrain the rectangle to the canvas area
    end_x = max(min(event.x, canvas.winfo_width()), 0)
    end_y = max(min(event.y, canvas.winfo_height()), 0)
    canvas.coords(rect_id, start_x + canvas_offset_x, start_y + canvas_offset_y, end_x, end_y)

def finish_crop(event):
    """Finish the crop selection and crop the image."""
    global pdf_image, scaled_image, image_scale, rect_id
    if pdf_image is None:
        messagebox.showerror("Error", "No PDF image loaded.")
        return

    try:
        # Get the rectangle coordinates on the canvas
        end_x, end_y = event.x - canvas_offset_x, event.y - canvas_offset_y
        x1, y1, x2, y2 = min(start_x, end_x), min(start_y, end_y), max(start_x, end_x), max(start_y, end_y)

        # Ensure coordinates are within the image bounds
        x1 = max(0, min(x1, scaled_image.width))
        y1 = max(0, min(y1, scaled_image.height))
        x2 = max(0, min(x2, scaled_image.width))
        y2 = max(0, min(y2, scaled_image.height))

        # Scale the coordinates back to the original image size
        x1 = int(x1 / image_scale)
        y1 = int(y1 / image_scale)
        x2 = int(x2 / image_scale)
        y2 = int(y2 / image_scale)

        # Crop the image with the scaled coordinates
        crop_box = (x1, y1, x2, y2)
        cropped_image = pdf_image.crop(crop_box)

        # Apply grayscale conversion if the checkbox is selected
        if grayscale_var.get():
            cropped_image = cropped_image.convert("L")  # "L" mode is for grayscale

        # Apply threshold if the checkbox is selected
        if threshold_var.get():
            threshold_level = 158  # Adjust this value as needed
            cropped_image = cropped_image.point(lambda p: 255 if p > threshold_level else 0)
            cropped_image = ImageOps.invert(cropped_image)

        # Ask the user where to save the cropped image
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")]
        )

        if save_path:
            # Save the cropped image if a path is provided
            cropped_image.save(save_path)
            messagebox.showinfo("Success", f"Cropped image saved to {save_path}.")
        else:
            # If the user cancels, reload and display the original image
            display_image(pdf_image)

        # Remove the crop selection rectangle from the canvas
        canvas.delete(rect_id)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to crop image: {e}")
        # Remove the rectangle even if an error occurs
        canvas.delete(rect_id)

# Initialize the main tkinter window
root = tk.Tk()
root.title("PDF Cropper")

# Global variables
pdf_image = None
tk_image = None
scaled_image = None
image_scale = 1
start_x = start_y = 0
rect_id = None

# Create GUI elements
frame = tk.Frame(root)
frame.pack(pady=10)

# Upload button
upload_button = tk.Button(frame, text="Upload PDF", command=load_pdf)
upload_button.grid(row=0, column=0, padx=5)

# Add checkboxes for grayscale and threshold near the upload button
grayscale_var = tk.IntVar()
threshold_var = tk.IntVar()

grayscale_checkbox = tk.Checkbutton(frame, text="Convert to Grayscale", variable=grayscale_var)
grayscale_checkbox.grid(row=0, column=1, padx=5)

threshold_checkbox = tk.Checkbutton(frame, text="Apply Threshold", variable=threshold_var)
threshold_checkbox.grid(row=0, column=2, padx=5)

# Create the canvas
canvas = tk.Canvas(root, width=600, height=800, bg="gray")
canvas.pack(pady=10)

# Bind mouse events to the canvas
canvas.bind("<ButtonPress-1>", start_crop)
canvas.bind("<B1-Motion>", update_crop)
canvas.bind("<ButtonRelease-1>", finish_crop)

# Maximize the window using state property
root.state('zoomed')

# Start the main event loop
root.mainloop()
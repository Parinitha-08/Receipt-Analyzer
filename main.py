import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import cv2
import pytesseract
import pandas as pd
import re

# ---------------- CONFIGURATION ----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

receipts_data = []
images_objs = []

# ---------------- CATEGORY FUNCTION ----------------
def categorize_vendor_text(text):
    text_lower = text.lower()
    if any(x in text_lower for x in ['brake', 'pedal', 'car', 'auto']):
        return 'Auto Parts'
    elif any(x in text_lower for x in ['pizza', 'burger', 'cafe', 'restaurant', 'food', 'groceries']):
        return 'Food'
    elif any(x in text_lower for x in ['flight', 'train', 'hotel', 'travel', 'uber', 'ola']):
        return 'Travel'
    elif any(x in text_lower for x in ['amazon', 'flipkart', 'mall', 'store', 'shopping']):
        return 'Shopping'
    elif any(x in text_lower for x in ['electricity', 'water', 'internet', 'phone', 'bill']):
        return 'Bills'
    else:
        return 'Others'

# ---------------- PROCESS IMAGE ----------------
def process_image(file_path):
    image = cv2.imread(file_path)
    if image is None:
        print(f"Cannot read {file_path}")
        return None, None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(gray)

    # ---------------- VENDOR ----------------
    vendor = "Unknown"
    for line in text.split('\n'):
        line = line.strip()
        if line and not re.search(r'receipt|invoice|bill|order', line, re.IGNORECASE):
            vendor = line
            break

    # ---------------- TOTAL AMOUNT ----------------
    total_amount = 'NA'
    currency = '$'
    lines = text.split('\n')
    for line in lines:
        if re.search(r'total|amount due|grand total|balance', line, re.IGNORECASE):
            amounts = re.findall(r'[\$₹]?(\d+(?:\.\d{1,2})?)', line)
            currencies = re.findall(r'([\$₹])', line)
            if amounts:
                total_amount = f"{currencies[0] if currencies else '$'}{max([float(a) for a in amounts]):.2f}"
                break

    # Fallback if no total line found
    if total_amount == 'NA':
        amounts = re.findall(r'[\$₹]?(\d+(?:\.\d{1,2})?)', text)
        currencies = re.findall(r'([\$₹])', text)
        if amounts:
            total_amount = f"{currencies[0] if currencies else '$'}{max([float(a) for a in amounts]):.2f}"

    # ---------------- DATE ----------------
    date_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4})|(\d{8})", text)
    date = date_match.group() if date_match else 'NA'

    # ---------------- CATEGORY ----------------
    category = categorize_vendor_text(text)

    receipts_data.append([vendor, date, total_amount, category])

    # Tkinter image
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(image_rgb)
    im_pil.thumbnail((280, 280))
    imgtk = ImageTk.PhotoImage(im_pil)
    images_objs.append(imgtk)
    info_text = f"Vendor: {vendor}\nDate: {date}\nTotal: {total_amount}\nCategory: {category}"
    return imgtk, info_text

# ---------------- GUI FUNCTIONS ----------------
def select_images():
    for widget in scrollable_frame.winfo_children():
        widget.destroy()
    images_objs.clear()
    receipts_data.clear()

    files = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
    if not files:
        return

    for f in files:
        imgtk, info = process_image(f)
        if imgtk:
            frame = tk.Frame(scrollable_frame, bd=2, relief="ridge", bg="#ffffff", highlightbackground="#4CAF50", highlightthickness=2)
            frame.pack(padx=10, pady=10, fill="x")

            lbl_img = tk.Label(frame, image=imgtk, bd=0)
            lbl_img.pack(side="left", padx=15, pady=15)

            lbl_text = tk.Label(frame, text=info, justify="left", font=("Helvetica", 11, "bold"), bg="#ffffff", fg="#333333")
            lbl_text.pack(side="left", padx=15)

def export_csv():
    if receipts_data:
        df = pd.DataFrame(receipts_data, columns=['Vendor', 'Date', 'Total Amount', 'Category'])
        df.to_csv("expenses.csv", index=False)
        print("CSV exported successfully!")

# ---------------- GUI SETUP ----------------
root = tk.Tk()
root.title("Stylish Receipt OCR")
root.geometry("1024x720")
root.configure(bg="#e8f0f2")

# Title Label
title = tk.Label(root, text="🧾 Receipt OCR Tool", font=("Helvetica", 18, "bold"), bg="#e8f0f2", fg="#2c3e50")
title.pack(pady=10)

# Buttons
btn_frame = tk.Frame(root, bg="#e8f0f2")
btn_frame.pack(pady=5)
btn_select = tk.Button(btn_frame, text="Select Receipts", command=select_images, bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"), width=18, height=2)
btn_select.pack(side="left", padx=15)
btn_export = tk.Button(btn_frame, text="Export CSV", command=export_csv, bg="#2196F3", fg="white", font=("Helvetica", 12, "bold"), width=18, height=2)
btn_export.pack(side="left", padx=15)

# Scrollable canvas
canvas = tk.Canvas(root, width=980, height=600, bg="#e8f0f2", highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#e8f0f2")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
scrollbar.pack(side="right", fill="y", pady=10)

root.mainloop()
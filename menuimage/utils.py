# utils.py

import cv2
import pytesseract
from PIL import Image
import requests
from django.conf import settings
from urllib.parse import quote
from urllib.parse import quote_plus



pytesseract.pytesseract.tesseract_cmd = r'C:\Users\arund\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    # Read the image using OpenCV
    img = cv2.imread(image_path)

    # Resize the image (adjust dimensions as needed)
    resized_img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Convert the image to grayscale
    gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding to enhance text visibility
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Increase contrast using histogram equalization
    equalized = cv2.equalizeHist(thresholded)

    # Return the preprocessed image without saving it
    return equalized

def analyze_image(image_path):
    # Preprocess the image
    preprocessed_image = preprocess_image(image_path)

    # Use Tesseract OCR to extract text from the preprocessed image
    extracted_text = pytesseract.image_to_string(Image.fromarray(preprocessed_image))

    # Split the extracted text into lines
    lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]

    return lines


def send_whatsapp_message(phone, template_name, params):
    base_url = "http://bhashsms.com/api/sendmsg.php"
    
    # Encode each parameter, carefully handling newlines for the items list
    encoded_params = []
    for param in params:
        if '\n' in str(param):  # This is likely the items list
            # Replace newlines with the URL-encoded version of "\n"
            encoded_param = quote_plus(str(param).replace('\n', '\\n'))
        else:
            encoded_param = quote_plus(str(param))
        encoded_params.append(encoded_param)
    
    params_str = ",".join(encoded_params)

    api_url = (
        f"{base_url}?"
        f"user={settings.BHASHSMS_USER}&"
        f"pass={settings.BHASHSMS_PASS}&"
        f"sender={settings.BHASHSMS_SENDER}&"
        f"phone={phone}&"
        f"text={template_name}&"
        f"priority=wa&"
        f"stype=normal&"
        f"Params={params_str}"
    )
    
    response = requests.get(api_url)

    print(api_url)
    print(response.text)
    # Check if the request was successful
    if response.status_code == 200:
        return True
    else:
        print(f"Error sending WhatsApp message: {response.text}")
        return False
    
# Working URL

# http://bhashsms.com/api/sendmsg.php?user=minglemenu&pass=password&sender=BUZWAP&phone=+917826884771&text=new_temp1&priority=wa&stype=normal&Params=Drink2Way,22,Dhanush,355.70,1.+COFFEE+x+1%5Cn2.+ESPRESSO+x+1%5Cn3.+ESPRESSO+WITH+MILK+x+1%5Cn4.+RISTRETO+x+1%5Cn5.+DOPIO+x+1%5Cn6.+DOPIO+WITH+MILK+x+1%5Cn7.+MACCHIATO+x+1%5Cn8.+AMERICANO+x+1%5Cn9.+AMERICANO+WITH+MILK+x+1

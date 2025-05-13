# 🍽️ MingleMenu

MingleMenu is a smart food ordering platform that digitizes restaurant menus using OCR and streamlines order processing via WhatsApp. It enables restaurants to receive and confirm orders directly on WhatsApp, making it efficient, easy, and user-friendly.

## 🌟 Features

- OCR-powered menu digitization
- QR-based menu access
- Seamless WhatsApp order integration (using WhatsApp Business API)
- Order confirmation via WhatsApp buttons
- Restaurant dashboard for order tracking
- Built with Django

## 🛠️ Tech Stack

- Backend: Django
- Frontend: HTML, CSS, JS
- Database: SQLite (dev) / PostgreSQL (prod)
- Integration: WhatsApp Business API
- Auth: Google Oauth

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Django 4.x
- WhatsApp Business API access
- OCR Library (Tesseract)

### Installation

```bash
git clone https://github.com/0xarun/v3-minglemenu.git
cd v3-minglemenu
pip install -r requirements.txt
python manage.py runserver
```

### Environment Variables
Create a `.env` file with:

```ini
WHATSAPP_API_KEY=your_key
OCR_ENGINE_PATH=/path/to/tesseract
```

## 📲 Usage

1. Restaurant uploads menu (image or PDF)
2. System digitizes it using OCR
3. Customers scan a QR to order
4. Restaurant gets order on WhatsApp and confirms with a button

Creator: [@0xarun](https://x.com/0xarun)

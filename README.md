# FoodExpress

A Django-based food delivery application that allows users to browse restaurants, order food, and track deliveries.

## Features

- User authentication and profile management
- Restaurant browsing and filtering
- Food ordering system with shopping cart
- Order tracking and history
- Responsive design

## Requirements

- Python 3.13
- Django 5.2
- Pillow
- Django Jazzmin

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Umaizabibi/FoodExpress.git
cd foodexpress
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Apply migrations:
```bash
python manage.py migrate
```

6. Create superuser (for admin access):
```bash
python manage.py createsuperuser
```

## Running the Application

1. Start the development server:
```bash
python manage.py runserver
```

2. Access the application at `http://127.0.0.1:8000/`
3. Admin interface available at `http://127.0.0.1:8000/admin/`

## Project Structure

```
foodexpress/
├── core/            # User authentication and profiles
├── restaurants/     # Restaurant and menu management
├── orders/          # Cart and order processing
├── foodexpress/     # Project settings
└── manage.py        # Django management script
```

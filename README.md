# InsiightPrep

InsiightPrep is a robust Django-based web application designed to provide students and educators with seamless access to high-quality examination question papers. The platform facilitates browsing papers by class level, term, and subject, and features integrated payment processing for premium content.

## 🚀 Key Features

- **Hierarchical Navigation**: Effortlessly browse papers through a structured hierarchy: Class (e.g., JHS 1, Basic 7) → Term → Subject.
- **Comprehensive Paper Management**: Support for various exam types including Mid-Term, End-Term, CAT, Assignments, Mock Exams, and Finals.
- **Integrated Payments**: Secure payment processing via **Paystack**, supporting Mobile Money (MTN, Vodafone, AirtelTigo).
- **Automated Fulfillment**: 
    - Instant PDF access upon successful payment.
    - Automated SMS delivery of paper passwords via **HTTPSMS Gateway**.
- **Free Samples**: Provision for free sample papers to allow users to preview content.
- **Analytics & Tracking**: Built-in download history and view tracking for administrative insights.
- **Cloud-Ready Storage**: Seamless integration with **Cloudinary** for scalable media (PDF) management and **Whitenoise** for static files.

## 🛠️ Tech Stack

- **Backend**: Python 3.x, Django 6.0
- **Database**: SQLite (Development) / PostgreSQL (Recommended for Production)
- **Media Storage**: Cloudinary (Documents/PDFs)
- **Static Files**: Whitenoise
- **SMS Gateway**: HTTPSMS API
- **Deployment**: Gunicorn, Procfile-ready for platforms like Render or Heroku.

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/InsiightPrep.git
   cd InsiightPrep
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the root directory and configure the following variables:
   ```env
   DEBUG=True
   SECRET_KEY=your_django_secret_key
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Paystack Configuration
   PAYSTACK_PUBLIC_KEY=pk_test_xxxxxxxx
   PAYSTACK_SECRET_KEY=sk_test_xxxxxxxx
   
   # HTTPSMS Configuration
   HTTPSMS_API_KEY=your_httpsms_api_key
   
   # Cloudinary Configuration
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   
   # Email Configuration (Optional but recommended for Contact Form)
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_app_password
   ```

5. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser** (to access the admin panel):
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Development Server**:
   ```bash
   python manage.py runserver
   ```

## 📂 Project Structure

- `InsiightPrep/`: Project configuration, core settings, and root URLs.
- `shop/`: Main application containing:
    - `models.py`: Database schema for Classes, Subjects, Papers, and Payments.
    - `views.py`: Logic for navigation, payment processing, and webhooks.
    - `templates/shop/`: HTML templates for the storefront.
- `templates/`: Global base templates.
- `media/`: Local storage fallback for uploads.
- `staticfiles/`: Directory for collected static assets.

## 📝 License

This project is licensed under the MIT License.

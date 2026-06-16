<div align="center">

<img src="https://img.shields.io/badge/-Django%204.2+-092E20?style=for-the-badge&logo=django&logoColor=white" />
<img src="https://img.shields.io/badge/-Python%203.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/-MySQL%208.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
<img src="https://img.shields.io/badge/-Bootstrap%205-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" />

<br /><br />

<h1>💊 MediCare</h1>
<p><strong>Medicine Management System for Modern Pharmacies</strong></p>
<p>A full-featured Django web application for inventory, sales, and reporting — built for pharmacists who need reliability and speed.</p>

<br />

[Features](#-features) · [Tech Stack](#-tech-stack) · [Quick Start](#-quick-start) · [Project Structure](#-project-structure) · [User Roles](#-user-roles)

</div>

---

## ✨ Features

| Module | What it does |
|---|---|
| 📊 **Dashboard** | Live analytics — usage trends, category breakdown, top medicines via Chart.js |
| 💊 **Medicine Management** | Full CRUD, search, filter, bulk delete, CSV & PDF export |
| 📦 **Inventory & Stock** | Real-time stock tracking, low-stock alerts, restock workflows, movement log |
| 🛒 **Sales & Dispensing** | POS-style interface with cart, discount support, and printable receipts |
| 📋 **Reports** | Sales, inventory, expiry, and category reports — all exportable |
| 🏭 **Supplier Management** | Track suppliers and their associated medicines |
| 🔔 **Notifications** | Automated alerts for low stock, expiring medicines, and system events |
| 🔐 **User Roles** | Admin, Pharmacist, and Staff with role-based access control |

---

## 🛠 Tech Stack

```
Backend      Python 3.11+  ·  Django 4.2+
Database     MySQL 8.0 via XAMPP
Frontend     Django Templates  ·  Bootstrap 5  ·  Chart.js  ·  jQuery
Icons        Font Awesome 6
```

---

## 🚀 Quick Start

### Prerequisites
- XAMPP (Apache + MySQL)
- Python 3.11+

---

### Step 1 — Start XAMPP

Launch the XAMPP Control Panel and start both **Apache** and **MySQL**.

---

### Step 2 — Create the Database

Open **phpMyAdmin** or the MySQL CLI and run:

```sql
CREATE DATABASE medicine_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### Step 3 — Configure Environment

In the project root, update your `.env` file:

```env
DEBUG=True
SECRET_KEY=your_secret_key_here
```

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 — Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Step 6 — Seed the Database

```bash
python manage.py seed_medicines
```

This creates:
- 12 medicine categories
- 20 default medicines (Paracetamol, Amoxicillin, Ibuprofen, and more)
- A default admin account (`admin` / `admin123`)

---

### Step 7 — (Optional) Create a Superuser

```bash
python manage.py createsuperuser
```

---

### Step 8 — Start the Server

```bash
python manage.py runserver
```

---

### Step 9 — Open the App

| URL | Description |
|---|---|
| http://127.0.0.1:8000 | Main application |
| http://127.0.0.1:8000/login/ | Login page |
| http://127.0.0.1:8000/admin/ | Django admin panel |

---

## 🔑 Default Accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |

> ⚠️ Change the default password before deploying to any shared or production environment.

---

## 📁 Project Structure

```
medicine_management/
│
├── manage.py
├── .env
├── requirements.txt
├── README.md
│
├── medicine_management/       # Core settings & routing
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── accounts/                  # Authentication, roles, user profiles
├── medicines/                 # Medicine CRUD & inventory logic
├── sales/                     # Sales processing & dispensing
├── reports/                   # Report generation & export
├── suppliers/                 # Supplier records
├── notifications/             # Alert & notification system
│
├── templates/                 # All HTML templates
├── static/                    # CSS, JavaScript, images
└── media/                     # User-uploaded files
```

---

## 👥 User Roles

| Role | Access |
|---|---|
| **Admin** | Full access — all modules, settings, and user management |
| **Pharmacist** | Manage medicines, process sales, view reports |
| **Staff** | View medicines and record usage only |

---

## 🔌 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/sales/api/medicine-info/` | `GET` | Returns medicine details by ID (JSON) |

---

## 📤 Export Options

- **Medicines list** → CSV / PDF
- **Sales reports** → CSV / PDF
- **Inventory reports** → CSV / PDF
- **Stock reports** → Print-ready
- **Sales receipts** → Print-ready

---

## 📄 License

This project is open for educational and personal use. See `LICENSE` for details.

---

<div align="center">
  <sub>Built with Django · Designed for pharmacists</sub>
</div>
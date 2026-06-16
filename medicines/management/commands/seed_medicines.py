from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from medicines.models import Category, Medicine
from suppliers.models import Supplier
import random
import string

User = get_user_model()

categories_data = [
    {'name': 'Antibiotic', 'icon': 'fa-bacteria', 'description': 'Antibiotic medications'},
    {'name': 'Painkiller', 'icon': 'fa-tablets', 'description': 'Pain relief medications'},
    {'name': 'Vitamin', 'icon': 'fa-vitamins', 'description': 'Vitamin and supplement medications'},
    {'name': 'Antiviral', 'icon': 'fa-virus', 'description': 'Antiviral medications'},
    {'name': 'Antifungal', 'icon': 'fa-fungus', 'description': 'Antifungal medications'},
    {'name': 'Cardiovascular', 'icon': 'fa-heart', 'description': 'Heart and blood pressure medications'},
    {'name': 'Diabetes', 'icon': 'fa-droplet', 'description': 'Diabetes medications'},
    {'name': 'Allergy', 'icon': 'fa-allergies', 'description': 'Allergy relief medications'},
    {'name': 'Antacid', 'icon': 'fa-stomach', 'description': 'Antacid and digestive medications'},
    {'name': 'Supplement', 'icon': 'fa-pills', 'description': 'Dietary supplements'},
    {'name': 'Respiratory', 'icon': 'fa-lungs', 'description': 'Respiratory medications'},
    {'name': 'Other', 'icon': 'fa-capsules', 'description': 'Other medications'},
]

medicines_data = [
    {'name': 'Paracetamol', 'generic_name': 'Acetaminophen', 'category': 'Painkiller', 'brand': 'Panadol', 'dosage_form': 'tablet', 'strength': '500mg', 'price': 0.50, 'stock_quantity': 100, 'expiry_date': date(2026, 12, 15), 'barcode_sku': 'MED001', 'image': 'https://placehold.co/400x400?text=Paracetamol'},
    {'name': 'Amoxicillin', 'generic_name': 'Amoxicillin Trihydrate', 'category': 'Antibiotic', 'brand': 'Amoxil', 'dosage_form': 'capsule', 'strength': '250mg', 'price': 1.20, 'stock_quantity': 80, 'expiry_date': date(2026, 9, 10), 'barcode_sku': 'MED002', 'image': 'https://placehold.co/400x400?text=Amoxicillin'},
    {'name': 'Ibuprofen', 'generic_name': 'Ibuprofen', 'category': 'Painkiller', 'brand': 'Advil', 'dosage_form': 'tablet', 'strength': '400mg', 'price': 0.80, 'stock_quantity': 120, 'expiry_date': date(2027, 3, 20), 'barcode_sku': 'MED003', 'image': 'https://placehold.co/400x400?text=Ibuprofen'},
    {'name': 'Metformin', 'generic_name': 'Metformin HCl', 'category': 'Diabetes', 'brand': 'Glucophage', 'dosage_form': 'tablet', 'strength': '500mg', 'price': 0.90, 'stock_quantity': 60, 'expiry_date': date(2026, 11, 5), 'barcode_sku': 'MED004', 'image': 'https://placehold.co/400x400?text=Metformin'},
    {'name': 'Atorvastatin', 'generic_name': 'Atorvastatin Calcium', 'category': 'Cardiovascular', 'brand': 'Lipitor', 'dosage_form': 'tablet', 'strength': '20mg', 'price': 2.50, 'stock_quantity': 50, 'expiry_date': date(2027, 1, 25), 'barcode_sku': 'MED005', 'image': 'https://placehold.co/400x400?text=Atorvastatin'},
    {'name': 'Omeprazole', 'generic_name': 'Omeprazole', 'category': 'Antacid', 'brand': 'Prilosec', 'dosage_form': 'capsule', 'strength': '20mg', 'price': 1.10, 'stock_quantity': 90, 'expiry_date': date(2026, 8, 30), 'barcode_sku': 'MED006', 'image': 'https://placehold.co/400x400?text=Omeprazole'},
    {'name': 'Cetirizine', 'generic_name': 'Cetirizine HCl', 'category': 'Allergy', 'brand': 'Zyrtec', 'dosage_form': 'tablet', 'strength': '10mg', 'price': 0.60, 'stock_quantity': 150, 'expiry_date': date(2027, 6, 15), 'barcode_sku': 'MED007', 'image': 'https://placehold.co/400x400?text=Cetirizine'},
    {'name': 'Azithromycin', 'generic_name': 'Azithromycin', 'category': 'Antibiotic', 'brand': 'Zithromax', 'dosage_form': 'tablet', 'strength': '500mg', 'price': 3.50, 'stock_quantity': 40, 'expiry_date': date(2026, 7, 12), 'barcode_sku': 'MED008', 'image': 'https://placehold.co/400x400?text=Azithromycin'},
    {'name': 'Vitamin C', 'generic_name': 'Ascorbic Acid', 'category': 'Vitamin', 'brand': 'C-1000', 'dosage_form': 'tablet', 'strength': '1000mg', 'price': 0.40, 'stock_quantity': 200, 'expiry_date': date(2027, 12, 1), 'barcode_sku': 'MED009', 'image': 'https://placehold.co/400x400?text=Vitamin+C'},
    {'name': 'Amlodipine', 'generic_name': 'Amlodipine Besylate', 'category': 'Cardiovascular', 'brand': 'Norvasc', 'dosage_form': 'tablet', 'strength': '5mg', 'price': 1.80, 'stock_quantity': 70, 'expiry_date': date(2026, 10, 18), 'barcode_sku': 'MED010', 'image': 'https://placehold.co/400x400?text=Amlodipine'},
    {'name': 'Aspirin', 'generic_name': 'Acetylsalicylic Acid', 'category': 'Cardiovascular', 'brand': 'Bayer', 'dosage_form': 'tablet', 'strength': '75mg', 'price': 0.30, 'stock_quantity': 110, 'expiry_date': date(2027, 2, 14), 'barcode_sku': 'MED011', 'image': 'https://placehold.co/400x400?text=Aspirin'},
    {'name': 'Doxycycline', 'generic_name': 'Doxycycline Hyclate', 'category': 'Antibiotic', 'brand': 'Vibramycin', 'dosage_form': 'capsule', 'strength': '100mg', 'price': 2.00, 'stock_quantity': 55, 'expiry_date': date(2026, 6, 28), 'barcode_sku': 'MED012', 'image': 'https://placehold.co/400x400?text=Doxycycline'},
    {'name': 'Loratadine', 'generic_name': 'Loratadine', 'category': 'Allergy', 'brand': 'Claritin', 'dosage_form': 'tablet', 'strength': '10mg', 'price': 0.70, 'stock_quantity': 130, 'expiry_date': date(2027, 4, 8), 'barcode_sku': 'MED013', 'image': 'https://placehold.co/400x400?text=Loratadine'},
    {'name': 'Metronidazole', 'generic_name': 'Metronidazole', 'category': 'Antibiotic', 'brand': 'Flagyl', 'dosage_form': 'tablet', 'strength': '400mg', 'price': 0.95, 'stock_quantity': 75, 'expiry_date': date(2026, 12, 22), 'barcode_sku': 'MED014', 'image': 'https://placehold.co/400x400?text=Metronidazole'},
    {'name': 'Lisinopril', 'generic_name': 'Lisinopril', 'category': 'Cardiovascular', 'brand': 'Zestril', 'dosage_form': 'tablet', 'strength': '10mg', 'price': 1.60, 'stock_quantity': 45, 'expiry_date': date(2027, 8, 5), 'barcode_sku': 'MED015', 'image': 'https://placehold.co/400x400?text=Lisinopril'},
    {'name': 'Pantoprazole', 'generic_name': 'Pantoprazole Sodium', 'category': 'Antacid', 'brand': 'Protonix', 'dosage_form': 'tablet', 'strength': '40mg', 'price': 1.30, 'stock_quantity': 85, 'expiry_date': date(2027, 5, 19), 'barcode_sku': 'MED016', 'image': 'https://placehold.co/400x400?text=Pantoprazole'},
    {'name': 'Fluconazole', 'generic_name': 'Fluconazole', 'category': 'Antifungal', 'brand': 'Diflucan', 'dosage_form': 'capsule', 'strength': '150mg', 'price': 4.00, 'stock_quantity': 30, 'expiry_date': date(2026, 11, 11), 'barcode_sku': 'MED017', 'image': 'https://placehold.co/400x400?text=Fluconazole'},
    {'name': 'Vitamin D3', 'generic_name': 'Cholecalciferol', 'category': 'Vitamin', 'brand': 'D3-1000', 'dosage_form': 'tablet', 'strength': '1000IU', 'price': 0.55, 'stock_quantity': 180, 'expiry_date': date(2027, 10, 3), 'barcode_sku': 'MED018', 'image': 'https://placehold.co/400x400?text=Vitamin+D3'},
    {'name': 'Oseltamivir', 'generic_name': 'Oseltamivir Phosphate', 'category': 'Antiviral', 'brand': 'Tamiflu', 'dosage_form': 'capsule', 'strength': '75mg', 'price': 8.50, 'stock_quantity': 25, 'expiry_date': date(2026, 9, 7), 'barcode_sku': 'MED019', 'image': 'https://placehold.co/400x400?text=Oseltamivir'},
    {'name': 'Salbutamol Inhaler', 'generic_name': 'Albuterol', 'category': 'Respiratory', 'brand': 'Ventolin', 'dosage_form': 'inhaler', 'strength': '100mcg', 'price': 6.00, 'stock_quantity': 20, 'expiry_date': date(2026, 8, 14), 'barcode_sku': 'MED020', 'image': 'https://placehold.co/400x400?text=Salbutamol+Inhaler'},
]


class Command(BaseCommand):
    help = 'Seed the database with default categories and medicines'

    def handle(self, *args, **options):
        self.stdout.write('Seeding categories...')
        cat_objects = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data['icon'], 'description': cat_data['description']}
            )
            cat_objects[cat.name] = cat
            if created:
                self.stdout.write(f'  Created category: {cat.name}')
            else:
                self.stdout.write(f'  Category exists: {cat.name}')

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='admin')
            self.stdout.write('  Created superuser: admin / admin123')

        self.stdout.write('Seeding medicines...')
        for med_data in medicines_data:
            category_name = med_data.pop('category')
            category = cat_objects.get(category_name)
            med, created = Medicine.objects.get_or_create(
                barcode_sku=med_data['barcode_sku'],
                defaults={**med_data, 'category': category, 'low_stock_threshold': 10}
            )
            if created:
                self.stdout.write(f'  Created medicine: {med.name}')
            else:
                self.stdout.write(f'  Medicine exists: {med.name}')

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(self.style.SUCCESS(f'  Categories: {Category.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Medicines: {Medicine.objects.count()}'))

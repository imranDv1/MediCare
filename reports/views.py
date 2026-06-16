from datetime import date, timedelta, datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count, F, Q
from django.http import HttpResponse, JsonResponse
from medicines.models import Medicine, Category, StockMovement
from sales.models import Sale, SaleItem
from suppliers.models import Supplier
import csv
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


@login_required
def reports_dashboard(request):
    return render(request, 'reports/reports_dashboard.html', {
        'total_medicines': Medicine.objects.count(),
        'total_categories': Category.objects.count(),
        'total_suppliers': Supplier.objects.count(),
        'total_sales': Sale.objects.count(),
    })


@login_required
def sales_report(request):
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.GET.get('end_date', date.today().isoformat())

    sales = Sale.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)

    daily_sales = []
    current = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    while current <= end:
        day_total = sales.filter(timestamp__date=current).aggregate(total=Sum('total'))['total'] or 0
        daily_sales.append({'date': current.isoformat(), 'total': float(day_total)})
        current += timedelta(days=1)

    labels = [d['date'] for d in daily_sales]
    data = [d['total'] for d in daily_sales]
    daily_sales_chart = {
        'labels': labels,
        'datasets': [{'label': 'Daily Sales', 'data': data, 'borderColor': '#4e8d6d', 'backgroundColor': 'rgba(78, 141, 109, 0.1)', 'fill': True, 'tension': 0.3}]
    }

    pmt_data = list(sales.values('payment_method').annotate(total=Sum('total')).annotate(count=Count('id')))
    payment_chart = {
        'labels': [p['payment_method'] for p in pmt_data],
        'datasets': [{'data': [float(p['total']) for p in pmt_data], 'backgroundColor': ['#4e8d6d', '#6ba3d6', '#d4a76a']}]
    }

    return render(request, 'reports/sales_report.html', {
        'sales': sales,
        'total_revenue': sales.aggregate(total=Sum('total'))['total'] or 0,
        'total_transactions': sales.count(),
        'start_date': start_date,
        'end_date': end_date,
        'daily_sales_json': json.dumps(daily_sales_chart),
        'payment_breakdown': json.dumps(payment_chart),
    })


@login_required
def inventory_report(request):
    medicines = Medicine.objects.select_related('category', 'supplier').all()
    total_stock_value = sum(m.price * m.stock_quantity for m in medicines)
    category_breakdown = Category.objects.annotate(
        medicine_count=Count('medicines'),
        total_stock=Sum('medicines__stock_quantity'),
        total_value=Sum(F('medicines__price') * F('medicines__stock_quantity'))
    )

    cat_names = [c.name for c in category_breakdown]
    cat_counts = [c.medicine_count for c in category_breakdown]
    inventory_category_chart = {
        'labels': cat_names,
        'datasets': [{'label': 'Medicine Count', 'data': cat_counts, 'backgroundColor': ['#4e8d6d', '#6ba3d6', '#d4a76a', '#e8836b', '#9b7bb5', '#6bb59a', '#d49b6a']}]
    }
    return render(request, 'reports/inventory_report.html', {
        'medicines': medicines,
        'total_stock_value': total_stock_value,
        'total_items': sum(m.stock_quantity for m in medicines),
        'category_breakdown': category_breakdown,
        'category_data_json': json.dumps(inventory_category_chart),
    })


@login_required
def expiry_report(request):
    days = int(request.GET.get('days', 30))
    today = date.today()
    expiry_date = today + timedelta(days=days)

    expiring = Medicine.objects.filter(expiry_date__gte=today, expiry_date__lte=expiry_date).order_by('expiry_date')
    expired = Medicine.objects.filter(expiry_date__lt=today)

    return render(request, 'reports/expiry_report.html', {
        'expiring': expiring,
        'expired': expired,
        'days': days,
        'today': today,
        'expiry_date': expiry_date,
    })


@login_required
def category_report(request):
    categories = Category.objects.annotate(
        medicine_count=Count('medicines'),
        total_stock=Sum('medicines__stock_quantity'),
        total_value=Sum(F('medicines__price') * F('medicines__stock_quantity'))
    )
    cat_labels = [c.name for c in categories]
    cat_data = [c.medicine_count for c in categories]
    category_chart_data = {
        'labels': cat_labels,
        'datasets': [{'label': 'Medicines per Category', 'data': cat_data, 'backgroundColor': ['#4e8d6d', '#6ba3d6', '#d4a76a', '#e8836b', '#9b7bb5', '#6bb59a', '#d49b6a']}]
    }
    return render(request, 'reports/category_report.html', {
        'categories': categories,
        'category_chart_data': json.dumps(category_chart_data),
    })


@login_required
def export_sales_csv(request):
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.GET.get('end_date', date.today().isoformat())

    sales = Sale.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Invoice No', 'Patient', 'Payment Method', 'Discount', 'Total', 'User', 'Date'])
    for sale in sales:
        writer.writerow([sale.invoice_no, sale.patient_name, sale.payment_method, sale.discount, sale.total, sale.user, sale.timestamp])

    return response


@login_required
def export_inventory_csv(request):
    medicines = Medicine.objects.select_related('category', 'supplier').all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Category', 'Stock', 'Price', 'Value', 'Expiry', 'Supplier'])
    for m in medicines:
        writer.writerow([m.name, m.category.name if m.category else '', m.stock_quantity, m.price, m.price * m.stock_quantity, m.expiry_date, m.supplier.name if m.supplier else ''])

    return response


@login_required
def export_sales_pdf(request):
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.GET.get('end_date', date.today().isoformat())

    sales = Sale.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(f'Sales Report: {start_date} to {end_date}', styles['Title']))
    elements.append(Spacer(1, 0.25 * inch))

    data = [['Invoice', 'Patient', 'Payment', 'Discount', 'Total', 'Date']]
    for sale in sales:
        data.append([sale.invoice_no, sale.patient_name, sale.payment_method, str(sale.discount), str(sale.total), sale.timestamp.strftime('%Y-%m-%d')])

    total = sales.aggregate(t=Sum('total'))['t'] or 0
    data.append(['', '', '', 'GRAND TOTAL', str(total), ''])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A73E8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#00BFA5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    return response


@login_required
def export_inventory_pdf(request):
    medicines = Medicine.objects.select_related('category').all()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph('Inventory Report', styles['Title']))
    elements.append(Spacer(1, 0.25 * inch))

    data = [['Name', 'Category', 'Stock', 'Price', 'Value', 'Expiry']]
    for m in medicines:
        data.append([m.name, m.category.name if m.category else '', str(m.stock_quantity), str(m.price), str(m.price * m.stock_quantity), m.expiry_date.isoformat()])

    total_value = sum(m.price * m.stock_quantity for m in medicines)
    data.append(['', '', '', 'TOTAL VALUE', str(total_value), ''])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A73E8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#00BFA5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    return response

import csv
import json
import uuid
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import F, Q, Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from notifications.models import Notification
from notifications.views import create_notification

from .forms import CategoryForm, MedicineForm, StockMovementForm
from .models import Category, Medicine, StockMovement

try:
    from sales.models import Sale, SaleItem
except ImportError:
    Sale = None
    SaleItem = None


def admin_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'admin',
        login_url='/login/',
    )(view_func)
    return decorated_view


def pharmacist_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.role in ['admin', 'pharmacist'],
        login_url='/login/',
    )(view_func)
    return decorated_view


@login_required
def dashboard(request):
    today = date.today()
    thirty_days = today + timedelta(days=30)

    total_medicines = Medicine.objects.count()
    out_of_stock_count = Medicine.objects.filter(stock_quantity__lte=0).count()
    low_stock_count = Medicine.objects.filter(
        Q(stock_quantity__gt=0) & Q(stock_quantity__lte=F('low_stock_threshold'))
    ).count()
    expiring_soon_count = Medicine.objects.filter(
        expiry_date__gte=today, expiry_date__lte=thirty_days
    ).count()

    today_sales_total = 0
    if Sale:
        today_sales = Sale.objects.filter(timestamp__date=today)
        total = today_sales.aggregate(t=Sum('total'))['t'] or 0
        today_sales_total = float(total)

    expiring_medicines = Medicine.objects.filter(
        expiry_date__gte=today, expiry_date__lte=thirty_days
    ).select_related('category').order_by('expiry_date')

    low_stock_medicines = Medicine.objects.filter(
        Q(stock_quantity__gt=0) & Q(stock_quantity__lte=F('low_stock_threshold'))
    ).select_related('category').order_by('stock_quantity')

    recent_movements = StockMovement.objects.select_related('medicine', 'user').order_by('-timestamp')[:10]

    categories = Category.objects.annotate(medicine_count=Count('medicines'))
    category_labels = json.dumps([c.name for c in categories])
    category_data = json.dumps([c.medicine_count for c in categories])

    top_medicines_labels = json.dumps([])
    top_medicines_data = json.dumps([])
    usage_last_30_days_labels = json.dumps([])
    usage_last_30_days_data = json.dumps([])

    if SaleItem:
        top_items = SaleItem.objects.values('medicine__name').annotate(
            total_qty=Sum('quantity')
        ).order_by('-total_qty')[:10]
        if top_items:
            top_medicines_labels = json.dumps([item['medicine__name'] for item in top_items])
            top_medicines_data = json.dumps([int(item['total_qty']) for item in top_items])

        usage_items = SaleItem.objects.filter(
            sale__timestamp__date__gte=today - timedelta(days=30)
        ).values('medicine__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:10]
        if usage_items:
            usage_last_30_days_labels = json.dumps([item['medicine__name'] for item in usage_items])
            usage_last_30_days_data = json.dumps([int(item['total_qty']) for item in usage_items])

    in_stock_count = total_medicines - low_stock_count - out_of_stock_count
    stock_status_labels = json.dumps(['In Stock', 'Low Stock', 'Out of Stock'])
    stock_status_data = json.dumps([in_stock_count, low_stock_count, out_of_stock_count])

    monthly_sales_labels = json.dumps([])
    monthly_sales_data = json.dumps([])
    monthly_movements_in = json.dumps([])
    monthly_movements_out = json.dumps([])
    monthly_movement_labels = json.dumps([])

    six_months_ago = today - timedelta(days=180)
    months = []
    for i in range(6):
        m = today.replace(day=1) - timedelta(days=30 * i)
        months.append(m.strftime('%Y-%m'))
    months.reverse()

    if Sale:
        monthly_sales = Sale.objects.filter(timestamp__date__gte=six_months_ago) \
            .annotate(month=TruncMonth('timestamp')) \
            .values('month').annotate(total=Sum('total')).order_by('month')
        sales_by_month = {s['month'].strftime('%Y-%m') if s['month'] else '': float(s['total']) for s in monthly_sales}
        monthly_sales_labels = json.dumps(months)
        monthly_sales_data = json.dumps([sales_by_month.get(m, 0) for m in months])

    movements = StockMovement.objects.filter(timestamp__date__gte=six_months_ago) \
        .annotate(month=TruncMonth('timestamp')) \
        .values('month', 'movement_type').annotate(total=Sum('quantity')).order_by('month')
    mov_in = {}
    mov_out = {}
    for mov in movements:
        key = mov['month'].strftime('%Y-%m') if mov['month'] else ''
        if mov['movement_type'] == 'IN':
            mov_in[key] = int(mov['total'])
        else:
            mov_out[key] = int(mov['total'])
    monthly_movement_labels = json.dumps(months)
    monthly_movements_in = json.dumps([mov_in.get(m, 0) for m in months])
    monthly_movements_out = json.dumps([mov_out.get(m, 0) for m in months])

    # Expiry notifications with dedup (once per day)
    expired_meds = Medicine.objects.filter(expiry_date__lte=today)
    for med in expired_meds:
        msg = f'"{med.name}" has expired on {med.expiry_date}.'
        if not Notification.objects.filter(
            notification_type='expired', message=msg, created_at__date=today,
        ).exists():
            create_notification('expired', msg)

    near_expiry_meds = Medicine.objects.filter(
        expiry_date__gt=today, expiry_date__lte=thirty_days,
    )
    for med in near_expiry_meds:
        msg = f'"{med.name}" expires in {med.days_until_expiry} days ({med.expiry_date}).'
        if not Notification.objects.filter(
            notification_type='near_expiry', message=msg, created_at__date=today,
        ).exists():
            create_notification('near_expiry', msg)

    context = {
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'out_of_stock_count': out_of_stock_count,
        'in_stock_count': in_stock_count,
        'today_sales_total': today_sales_total,
        'expiring_medicines': expiring_medicines,
        'low_stock_medicines': low_stock_medicines,
        'recent_movements': recent_movements,
        'category_labels': category_labels,
        'category_data': category_data,
        'top_medicines_labels': top_medicines_labels,
        'top_medicines_data': top_medicines_data,
        'usage_last_30_days_labels': usage_last_30_days_labels,
        'usage_last_30_days_data': usage_last_30_days_data,
        'stock_status_labels': stock_status_labels,
        'stock_status_data': stock_status_data,
        'monthly_sales_labels': monthly_sales_labels,
        'monthly_sales_data': monthly_sales_data,
        'monthly_movement_labels': monthly_movement_labels,
        'monthly_movements_in': monthly_movements_in,
        'monthly_movements_out': monthly_movements_out,
    }
    return render(request, 'medicines/dashboard.html', context)


@login_required
def medicine_list(request):
    medicines = Medicine.objects.select_related('category', 'supplier').all()

    search = request.GET.get('search', '')
    if search:
        medicines = medicines.filter(
            Q(name__icontains=search) |
            Q(generic_name__icontains=search) |
            Q(brand__icontains=search)
        )

    category_id = request.GET.get('category', '')
    if category_id:
        medicines = medicines.filter(category_id=category_id)

    status = request.GET.get('status', '')
    if status == 'low':
        medicines = medicines.filter(
            Q(stock_quantity__gt=0) & Q(stock_quantity__lte=F('low_stock_threshold'))
        )
    elif status == 'out':
        medicines = medicines.filter(stock_quantity__lte=0)
    elif status == 'in':
        medicines = medicines.filter(stock_quantity__gt=F('low_stock_threshold'))

    expiry_start = request.GET.get('expiry_start', '')
    expiry_end = request.GET.get('expiry_end', '')
    if expiry_start:
        medicines = medicines.filter(expiry_date__gte=expiry_start)
    if expiry_end:
        medicines = medicines.filter(expiry_date__lte=expiry_end)

    if request.method == 'POST' and request.POST.get('action') == 'delete':
        selected_ids = request.POST.getlist('selected_ids')
        if selected_ids:
            deleted = Medicine.objects.filter(id__in=selected_ids).delete()[0]
            messages.success(request, f'{deleted} medicine(s) deleted successfully.')
            return redirect('medicine_list')

    paginator = Paginator(medicines, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search': search,
        'category_id': category_id,
        'status': status,
        'expiry_start': expiry_start,
        'expiry_end': expiry_end,
    }
    return render(request, 'medicines/medicine_list.html', context)


@login_required
@pharmacist_required
def medicine_create(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save(commit=False)
            medicine.created_by = request.user
            if not medicine.barcode_sku:
                medicine.barcode_sku = str(uuid.uuid4()).replace('-', '').upper()[:12]
            medicine.save()

            StockMovement.objects.create(
                medicine=medicine,
                movement_type='IN',
                quantity=medicine.stock_quantity,
                note='Initial stock',
                user=request.user,
            )

            messages.success(request, f'Medicine "{medicine.name}" created successfully.')
            return redirect('medicine_list')
    else:
        form = MedicineForm()

    return render(request, 'medicines/medicine_form.html', {'form': form, 'title': 'Add Medicine'})


@login_required
@pharmacist_required
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f'Medicine "{medicine.name}" updated successfully.')
            return redirect('medicine_detail', pk=medicine.pk)
    else:
        form = MedicineForm(instance=medicine)

    return render(request, 'medicines/medicine_form.html', {'form': form, 'title': 'Edit Medicine'})


@login_required
def medicine_detail(request, pk):
    medicine = get_object_or_404(
        Medicine.objects.select_related('category', 'supplier', 'created_by'), pk=pk
    )
    stock_movements = medicine.stock_movements.select_related('user').order_by('-timestamp')[:20]

    related_medicines = Medicine.objects.filter(category=medicine.category).exclude(pk=medicine.pk)[:5]

    sale_items = []
    if SaleItem:
        sale_items = SaleItem.objects.filter(medicine=medicine).select_related('sale').order_by('-sale__timestamp')[:20]

    six_months_ago = date.today() - timedelta(days=180)
    stock_history = medicine.stock_movements.filter(timestamp__date__gte=six_months_ago).order_by('timestamp')

    initial_stock = medicine.stock_quantity
    for m in stock_history:
        initial_stock += -m.quantity if m.movement_type == 'IN' else m.quantity

    running = initial_stock
    hist_labels = []
    hist_data = []
    for m in stock_history:
        running += m.quantity if m.movement_type == 'IN' else -m.quantity
        hist_labels.append(m.timestamp.strftime('%b %d'))
        hist_data.append(running)

    stock_history_labels = json.dumps(hist_labels)
    stock_history_data = json.dumps(hist_data)

    context = {
        'medicine': medicine,
        'stock_movements': stock_movements,
        'related_medicines': related_medicines,
        'sale_items': sale_items,
        'stock_history': stock_history,
        'stock_history_labels': stock_history_labels,
        'stock_history_data': stock_history_data,
    }
    return render(request, 'medicines/medicine_detail.html', context)


@login_required
@admin_required
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        medicine.delete()
        messages.success(request, f'Medicine "{medicine.name}" deleted successfully.')
        return redirect('medicine_list')

    return render(request, 'medicines/medicine_confirm_delete.html', {'medicine': medicine})


@login_required
def stock_list(request):
    medicines = Medicine.objects.select_related('category').all().order_by('stock_quantity')
    low_stock_alerts = [m for m in medicines if m.status == 'low_stock']
    out_of_stock_alerts = [m for m in medicines if m.status == 'out_of_stock']

    context = {
        'medicines': medicines,
        'low_stock_alerts': low_stock_alerts,
        'out_of_stock_alerts': out_of_stock_alerts,
    }
    return render(request, 'medicines/stock_list.html', context)


@login_required
@pharmacist_required
def restock_medicine(request):
    if request.method == 'POST':
        medicine_id = request.POST.get('medicine_id')
        quantity = request.POST.get('quantity')
        note = request.POST.get('note', '')

        try:
            medicine = Medicine.objects.get(pk=medicine_id)
            quantity = int(quantity)

            if quantity <= 0:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Quantity must be positive.'}, status=400)
                messages.error(request, 'Quantity must be positive.')
                return redirect('stock_list')

            medicine.stock_quantity += quantity
            medicine.save()

            StockMovement.objects.create(
                medicine=medicine,
                movement_type='IN',
                quantity=quantity,
                note=note or 'Restocked',
                user=request.user,
            )

            create_notification('system', f'{medicine.name} restocked with {quantity} units by {request.user.get_full_name() or request.user.username}.')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'new_stock': medicine.stock_quantity,
                    'message': f'{medicine.name} restocked with {quantity} units.',
                })

            messages.success(request, f'{medicine.name} restocked with {quantity} units.')
            return redirect('stock_list')

        except Medicine.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Medicine not found.'}, status=404)
            messages.error(request, 'Medicine not found.')
            return redirect('stock_list')
        except (ValueError, TypeError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid quantity.'}, status=400)
            messages.error(request, 'Invalid quantity.')
            return redirect('stock_list')

    return redirect('stock_list')


@login_required
@admin_required
def medicine_bulk_delete(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        if selected_ids:
            deleted = Medicine.objects.filter(id__in=selected_ids).delete()[0]
            messages.success(request, f'{deleted} medicine(s) deleted successfully.')
        else:
            messages.warning(request, 'No medicines selected.')
    return redirect('medicine_list')


@login_required
@pharmacist_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="medicines.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Name', 'Generic Name', 'Category', 'Brand', 'Dosage Form', 'Strength',
        'Price', 'Stock Quantity', 'Low Stock Threshold', 'Manufacturing Date',
        'Expiry Date', 'Barcode/SKU', 'Status', 'Supplier', 'Description',
        'Created At', 'Updated At', 'Created By',
    ])

    medicines = Medicine.objects.select_related('category', 'supplier', 'created_by').all()
    for m in medicines:
        writer.writerow([
            m.name,
            m.generic_name,
            m.category.name if m.category else '',
            m.brand,
            m.get_dosage_form_display(),
            m.strength,
            m.price,
            m.stock_quantity,
            m.low_stock_threshold,
            m.manufacturing_date.strftime('%Y-%m-%d') if m.manufacturing_date else '',
            m.expiry_date.strftime('%Y-%m-%d') if m.expiry_date else '',
            m.barcode_sku,
            m.status.replace('_', ' ').title(),
            m.supplier.name if m.supplier else '',
            m.description,
            m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else '',
            m.updated_at.strftime('%Y-%m-%d %H:%M') if m.updated_at else '',
            m.created_by.get_full_name() or m.created_by.username if m.created_by else '',
        ])

    return response


@login_required
@pharmacist_required
def export_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, Table, TableStyle

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="medicines.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4), title='Medicines Report')
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        alignment=TA_CENTER, spaceAfter=20,
    )
    elements.append(Paragraph('Medicines Report', title_style))
    elements.append(Spacer(1, 10))

    medicines = Medicine.objects.select_related('category').all()

    data = [['Name', 'Category', 'Strength', 'Price', 'Stock', 'Expiry', 'Status']]
    for m in medicines:
        data.append([
            m.name,
            m.category.name if m.category else '-',
            m.strength,
            str(m.price),
            str(m.stock_quantity),
            m.expiry_date.strftime('%Y-%m-%d') if m.expiry_date else '-',
            m.status.replace('_', ' ').title(),
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90D9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)

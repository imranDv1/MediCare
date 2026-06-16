import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from medicines.models import Medicine, StockMovement
from notifications.views import create_notification

from .forms import SaleForm
from .models import Sale, SaleItem


def pharmacist_required(view_func):
    decorated_view = user_passes_test(
        lambda u: u.is_authenticated and u.role in ['admin', 'pharmacist', 'staff'],
        login_url='/login/',
    )(view_func)
    return decorated_view


@login_required
def sales_list(request):
    query = request.GET.get('q', '')
    sales = Sale.objects.select_related('user').all()

    if query:
        sales = sales.filter(
            Q(invoice_no__icontains=query) |
            Q(patient_name__icontains=query)
        )

    paginator = Paginator(sales, 20)
    page = request.GET.get('page', 1)
    sales_page = paginator.get_page(page)

    context = {
        'sales': sales_page,
        'query': query,
        'is_paginated': sales_page.has_other_pages(),
    }
    return render(request, 'sales/sales_list.html', context)


@login_required
@pharmacist_required
def create_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)

        try:
            items_data = data.get('items', [])
            if not items_data:
                return JsonResponse({'success': False, 'error': 'No items provided.'}, status=400)

            payment_method = data.get('payment_method', 'cash')
            patient_name = data.get('patient_name', '')
            doctor_ref = data.get('doctor_ref', '')
            discount = float(data.get('discount', 0))

            if discount < 0:
                return JsonResponse({'success': False, 'error': 'Discount cannot be negative.'}, status=400)

            medicine_ids = [item['medicine_id'] for item in items_data]
            medicines = Medicine.objects.filter(id__in=medicine_ids)
            medicine_map = {m.id: m for m in medicines}

            if len(medicine_map) != len(medicine_ids):
                return JsonResponse({'success': False, 'error': 'One or more medicines not found.'}, status=400)

            sale_items = []
            subtotal = 0.0

            for item in items_data:
                med_id = item['medicine_id']
                qty = int(item['quantity'])

                if qty <= 0:
                    return JsonResponse({'success': False, 'error': f'Invalid quantity for {medicine_map[med_id].name}.'}, status=400)

                medicine = medicine_map[med_id]

                if medicine.stock_quantity < qty:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient stock for {medicine.name}. Available: {medicine.stock_quantity}, requested: {qty}.',
                    }, status=400)

                unit_price = float(item.get('unit_price', float(medicine.price)))
                item_subtotal = round(qty * unit_price, 2)
                subtotal += item_subtotal

                sale_items.append({
                    'medicine': medicine,
                    'quantity': qty,
                    'unit_price': round(unit_price, 2),
                    'subtotal': item_subtotal,
                })

            subtotal = round(subtotal, 2)
            discount_amount = round(subtotal * (discount / 100), 2) if discount > 0 else round(discount, 2)
            total = round(subtotal - discount_amount, 2)

            if total < 0:
                return JsonResponse({'success': False, 'error': 'Total cannot be negative.'}, status=400)

            for attempt in range(5):
                try:
                    with transaction.atomic():
                        prefix = timezone.localdate().strftime('INV-%Y%m%d-')
                        last_invoice = Sale.objects.filter(invoice_no__startswith=prefix).select_for_update().order_by('invoice_no').last()
                        if last_invoice:
                            last_num = int(last_invoice.invoice_no.rsplit('-', 1)[-1])
                            invoice_no = f'{prefix}{last_num + 1:04d}'
                        else:
                            invoice_no = f'{prefix}0001'

                        sale = Sale.objects.create(
                            invoice_no=invoice_no,
                            patient_name=patient_name,
                            doctor_ref=doctor_ref,
                            payment_method=payment_method,
                            discount=discount,
                            subtotal=subtotal,
                            total=total,
                            user=request.user,
                        )

                        for si in sale_items:
                            SaleItem.objects.create(
                                sale=sale,
                                medicine=si['medicine'],
                                quantity=si['quantity'],
                                unit_price=si['unit_price'],
                                subtotal=si['subtotal'],
                            )

                            Medicine.objects.filter(id=si['medicine'].id).update(
                                stock_quantity=F('stock_quantity') - si['quantity']
                            )

                            StockMovement.objects.create(
                                medicine=si['medicine'],
                                movement_type='OUT',
                                quantity=si['quantity'],
                                note=f'Sale #{invoice_no}',
                                user=request.user,
                            )
                    break
                except IntegrityError:
                    if attempt == 4:
                        raise

            create_notification('new_sale', f'New sale #{invoice_no} - ${total:.2f}', user=request.user)
            sold_ids = [si['medicine'].id for si in sale_items]
            low_stock = Medicine.objects.filter(id__in=sold_ids, stock_quantity__lte=F('low_stock_threshold'))
            for med in low_stock:
                create_notification('low_stock', f'Only {med.stock_quantity} left in stock for {med.name}.', user=request.user)

            return JsonResponse({'success': True, 'sale_id': sale.id, 'invoice_no': invoice_no})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    medicines = Medicine.objects.filter(stock_quantity__gt=0).order_by('name')
    form = SaleForm()
    context = {
        'form': form,
        'medicines': medicines,
    }
    return render(request, 'sales/create_sale.html', context)


@login_required
@pharmacist_required
def sale_detail(request, pk):
    sale = get_object_or_404(
        Sale.objects.select_related('user').prefetch_related('items__medicine'),
        pk=pk,
    )
    return render(request, 'sales/sale_detail.html', {'sale': sale})


@login_required
@pharmacist_required
def print_receipt(request, pk):
    sale = get_object_or_404(
        Sale.objects.select_related('user').prefetch_related('items__medicine'),
        pk=pk,
    )
    return render(request, 'sales/receipt.html', {'sale': sale})


@login_required
@pharmacist_required
def get_medicine_info(request):
    medicine_id = request.GET.get('medicine_id')
    if not medicine_id:
        return JsonResponse({'error': 'medicine_id is required.'}, status=400)

    medicine = get_object_or_404(Medicine, pk=medicine_id)
    return JsonResponse({
        'id': medicine.id,
        'name': medicine.name,
        'price': float(medicine.price),
        'stock': medicine.stock_quantity,
        'strength': medicine.strength,
        'generic_name': medicine.generic_name,
    })

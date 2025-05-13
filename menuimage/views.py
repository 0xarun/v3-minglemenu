from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from .models import Store, CartItem, Payment, BusinessOwner, Offer, Advertisement, CouponCode, Order
from .forms import StoreForm, BusinessOwnerForm, MenuItemForm, EditTextForm, ItemPriceFormSet, OfferForm, AdvertisementForm, CouponCodeForm
from .utils import analyze_image, send_whatsapp_message
from django.utils import timezone
from django.conf import settings
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
from django.db.models import Sum, F, Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.sites.shortcuts import get_current_site
import random
import string
import json
import os
import uuid
import re
import qrcode
from io import BytesIO
import base64
from itertools import zip_longest



@transaction.atomic
def create_store(store_name, edited_text, owner):
    store_id = Store.generate_store_id()
    store = Store(
        store_id=store_id,
        store_name=store_name,
        edited_text=edited_text,
        owner=owner
    )
    store.save()
    return store

def landing_page(request):
    query = request.GET.get('q')
    result = None

    user_stores = []
    if request.user.is_authenticated:
        user_stores = Store.objects.filter(owner=request.user)
    
    all_stores = []
    all_stores = Store.objects.all()

    if query:
        result = Store.objects.filter(Q(store_name__icontains=query))
    else:
        result = Store.objects.none()
 

    context = {
        'user_stores': user_stores,
        'all_stores': all_stores,
        'query': query,
        'result': result,

    }
    return render(request, 'menuimage/home.html', context)

@login_required
@ensure_csrf_cookie
def dashboard_view(request, store_id):
    store = get_object_or_404(Store, store_id=store_id, owner=request.user)
    business_owner, created = BusinessOwner.objects.get_or_create(store=store)

    if request.method == 'POST' and request.POST.get('action') == 'update_business_info':
        form = BusinessOwnerForm(request.POST, instance=business_owner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Business information updated successfully.')
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    form = BusinessOwnerForm(instance=business_owner)
    # Fetch data for each section
    recent_orders = Order.objects.filter(store=store).order_by('-created_at')[:5].prefetch_related('items')
    total_revenue = Order.objects.filter(store=store).aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Get menu items
    menu_items = []
    lines = [line.strip() for line in store.edited_text.split('\n') if line.strip()]
    for line in lines:
        match = re.match(r'^(.*?)\s*(\d+(\.\d{1,2})?)$', line)
        if match:
            item = match.group(1).strip()
            price = match.group(2)
            menu_items.append((item, price))
        elif not line[0].isdigit():
            menu_items.append((line, ''))

    offers = Offer.objects.filter(store=store)
    advertisements = Advertisement.objects.filter(store=store)
    coupons = CouponCode.objects.filter(store=store)

    offer_form = OfferForm()
    ad_form = AdvertisementForm()
    coupon_form = CouponCodeForm()

    # Get popular items (you'll need to implement this logic)
    popular_items = []  # Implement your logic to get popular items

    context = {
        'store': store,
        'form': form,
        'recent_orders': recent_orders,
        'total_revenue': total_revenue,
        'menu_items': menu_items,
        'business_owner': business_owner,
        'popular_items': popular_items,
        'form': BusinessOwnerForm(instance=business_owner),
        'offers': offers,
        'advertisements': advertisements,
        'coupons': coupons,
        'offer_form': offer_form,
        'ad_form': ad_form,
        'coupon_form': coupon_form,
        'edit_menu_url': reverse('edit_confirm_page', args=[store_id]),
        'fix_menu_url': reverse('fix_menu', args=[store_id]),
        'business_info_url': reverse('business_info', args=[store_id]),
        'generate_qr_url': reverse('generate_qr', args=[store_id]),
    }

    if request.user.is_authenticated:
        social_account = request.user.socialaccount_set.filter(provider='google').first()
        if social_account:
            context['profile_image_url'] = social_account.extra_data['picture']

    return render(request, 'menuimage/dashboard.html', context)


@login_required
def image_recognition_view(request):
    if request.method == 'POST':
        store_name = request.POST.get('store_name')
        if not store_name:
            messages.error(request, 'Store name is required.')
            return render(request, 'menuimage/home.html', {'form': EditTextForm()})

        menu_image = request.FILES.get('menu_image')
        if not menu_image:
            messages.error(request, 'Menu image is required.')
            return render(request, 'menuimage/home.html', {'form': EditTextForm()})

        image_path = os.path.join(settings.MEDIA_ROOT, 'uploaded_images', menu_image.name)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        with open(image_path, 'wb') as destination:
            for chunk in menu_image.chunks():
                destination.write(chunk)

        extracted_text = analyze_image(image_path)

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                with transaction.atomic():
                    store = create_store(store_name, '\n'.join(extracted_text), request.user)
                return redirect('business_info', store_id=store.store_id)
            except Exception as e:
                if attempt == max_attempts - 1:
                    messages.error(request, f'An error occurred while creating the store: {str(e)}')
                    return render(request, 'menuimage/home.html', {'form': EditTextForm()})

    return render(request, 'menuimage/home.html', {'form': EditTextForm()})

@login_required
def business_info_view(request, store_id):
    store = get_object_or_404(Store, store_id=store_id, owner=request.user)
    business_owner, created = BusinessOwner.objects.get_or_create(store=store)

    if request.method == 'POST':
        form = BusinessOwnerForm(request.POST, instance=business_owner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Business information updated successfully.')
            return redirect('dashboard', store_id=store_id)
        else:
            messages.error(request, 'Error updating business information. Please check the form and try again.')
    else:
        form = BusinessOwnerForm(instance=business_owner)
    
    context = {
        'form': form,
        'store': store,
    }
    return render(request, 'menuimage/business_info.html', context)

def manual_menu_creation_view(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST)
        formset = ItemPriceFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            store_name = form.cleaned_data['store_name']
            items_and_prices = []
            for item_form in formset:
                item_name = item_form.cleaned_data.get('item_name')
                item_price = item_form.cleaned_data.get('item_price')
                if item_name and item_price:
                    items_and_prices.append(f"{item_name} {item_price}")
            
            store_id = Store.generate_store_id()
            store = Store.objects.create(
                store_id=store_id,
                store_name=store_name,
                edited_text='\n'.join(items_and_prices),
                owner=request.user
            )
            return redirect('business_info', store_id=store.store_id)
    else:
        form = MenuItemForm()
        formset = ItemPriceFormSet()
    
    return render(request, 'menuimage/new_menu.html', {'form': form, 'formset': formset})


def store_page_view(request, store_id):
    store = get_object_or_404(Store, store_id=store_id)
    user_stores = Store.objects.filter(owner=request.user) if request.user.is_authenticated else []

    # Use the menu_items attribute if it exists, otherwise parse the edited_text
    if hasattr(store, 'menu_items') and store.menu_items:
        menu_items = store.menu_items
    else:
        # Use the original logic to parse menu items
        menu_items = []
        lines = [line.strip() for line in store.edited_text.split('\n') if line.strip()]
        for line in lines:
            match = re.match(r'^(.*?)\s*(\d+(\.\d{1,2})?)$', line)
            if match:
                item = match.group(1).strip()
                price = match.group(2)
                if item and not item[0].isdigit():
                    menu_items.append((item, price))
            elif not line[0].isdigit():
                menu_items.append((line, ''))

    offers = Offer.objects.filter(store=store, is_active=True)
    advertisements = Advertisement.objects.filter(store=store, is_active=True)
    coupons = CouponCode.objects.filter(store=store, is_active=True)


    context = {
        'store': store,
        'menu_items': menu_items,
        'user_stores': user_stores,
        'is_owner': request.user.is_authenticated and store.owner == request.user,
        'offers': offers,
        'advertisements': advertisements,
        'coupons': coupons,
    }

    if request.user.is_authenticated:
        social_account = request.user.socialaccount_set.filter(provider='google').first()
        if social_account:
            context['profile_image_url'] = social_account.extra_data['picture']

    return render(request, 'menuimage/new_store.html', context)

def fix_menu(request, store_id):
    store = get_object_or_404(Store, store_id=store_id)
    lines = [line.strip() for line in store.edited_text.split('\n') if line.strip()]
    
    # Get the current fix method from the session, or default to 0
    fix_method = request.session.get(f'fix_method_{store_id}', 0)
    
    menu_items = []
    
    if fix_method == 0:
        # Case 1: Try to parse "Item Name $Price" pattern
        for line in lines:
            match = re.match(r'^(.*?)\s*\$?\s*(\d+(\.\d{1,2})?)$', line)
            if match:
                item = match.group(1).strip()
                price = match.group(2)
                if item and not item[0].isdigit():
                    menu_items.append((item, price))
            else:
                menu_items.append((line, ''))
    
    elif fix_method == 1:
        # Case 2: Try to separate items and prices if they're on separate lines
        items = [line for line in lines if not line[0].isdigit()]
        prices = [line for line in lines if line[0].isdigit()]
        menu_items = list(zip(items, prices))
    
    elif fix_method == 3:
        # New case for multiple items and prices on the same line
        for line in lines:
            # Split the line by common separators
            items = re.split(r'[|¢}]', line)
            for item in items:
                # Remove any leading/trailing whitespace and special characters
                item = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', item.strip())
                # Try to find a price in the item
                match = re.search(r'(\d+(\.\d{1,2})?)', item)
                if match:
                    price = match.group(1)
                    # Remove the price and any non-alphanumeric characters before it from the item name
                    name = re.sub(r'\s*[\W_]*\s*\d+(\.\d{1,2})?\s*$', '', item).strip()
                    menu_items.append((name, price))
                else:
                    # If no price is found, add the item without a price
                    menu_items.append((item, ''))

    else:
        # Case 3: Use the original parsing logic
        for line in lines:
            match = re.match(r'^(.*?)\s*(\d+(\.\d{1,2})?)$', line)
            if match:
                item = match.group(1).strip()
                price = match.group(2)
                if item and not item[0].isdigit():
                    menu_items.append((item, price))
            elif not line[0].isdigit():
                menu_items.append((line, ''))
    
    # Increment the fix method for next time
    next_fix_method = (fix_method + 1) % 4
    request.session[f'fix_method_{store_id}'] = next_fix_method
    
    # Update the store's menu_items
    store.menu_items = menu_items
    store.save()
    
    messages.info(request, 'Menu format updated. If it looks incorrect, click "Fix Menu" again.')
    return redirect('store_page', store_id=store_id)
    
def add_to_cart(request, store_id):
    data = json.loads(request.body)
    item_name = data.get('item_name')
    price = data.get('price')
    
    price_decimal = Decimal(price.replace('$', ''))

    store = get_object_or_404(Store, store_id=store_id)
    cart_id = request.session.get(f'cart_id_{store_id}')

    if not cart_id:
        cart_id = str(uuid.uuid4())
        request.session[f'cart_id_{store_id}'] = cart_id

    cart_item, created = CartItem.objects.get_or_create(
        cart_id=cart_id,
        store=store,
        item_name=item_name,
        defaults={'price': price}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({'status': 'success'})

def view_cart(request, store_id):
    store = get_object_or_404(Store, store_id=store_id)
    cart_id = request.session.get(f'cart_id_{store_id}')
    cart_items = CartItem.objects.filter(cart_id=cart_id, store=store)
    total = sum(item.total_price() for item in cart_items)

    return render(request, 'menuimage/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'store': store,
    })

def update_cart(request, store_id):
    if request.method == 'POST':
        store = get_object_or_404(Store, store_id=store_id)
        cart_id = request.session.get(f'cart_id_{store_id}')
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')

        item = get_object_or_404(CartItem, id=item_id, cart_id=cart_id, store=store)

        if action == 'increase':
            item.quantity += 1
        elif action == 'decrease':
            item.quantity -= 1
            if item.quantity <= 0:
                item.delete()
                return redirect('view_cart', store_id=store_id)

        item.save()

    return redirect('view_cart', store_id=store_id)


def place_order(request, store_id):
    if request.method == 'POST':
        store = get_object_or_404(Store, store_id=store_id)
        cart_id = request.session.get(f'cart_id_{store_id}')
        cart_items = CartItem.objects.filter(cart_id=cart_id, store=store)

        total_price = cart_items.annotate(
            item_total=F('price') * F('quantity')
        ).aggregate(Sum('item_total'))['item_total__sum'] or Decimal('0')

        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        order_type = request.POST.get('order_type')
        payment_method = request.POST.get('payment_method')

        if not all([full_name, phone_number, order_type, payment_method]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('view_cart', store_id=store_id)

        order = Order.objects.create(
            store=store,
            total_price=total_price,
            customer_name=full_name,
            customer_phone=phone_number,
            order_type=order_type,
            payment_method=payment_method,
            status='PENDING'
        )
        
        # Associate cart items with the order
        for cart_item in cart_items:
            order.items.create(
                item_name=cart_item.item_name,
                price=cart_item.price,
                quantity=cart_item.quantity
            )

        if payment_method == 'cash':
            order.status = 'COMPLETED'
            order.save()
            cart_items.delete()
            if f'cart_id_{store_id}' in request.session:
                del request.session[f'cart_id_{store_id}']
            return redirect('order_success', store_id=store_id, order_id=order.id)
        elif payment_method == 'upi':
            return JsonResponse({'status': 'success', 'redirect_url': reverse('initiate_payment', args=[store_id, order.id])})

    return redirect('view_cart', store_id=store_id)


def order_success(request, store_id, order_id):
    store = get_object_or_404(Store, store_id=store_id)
    order = get_object_or_404(Order, id=order_id, store=store)
    order_items = order.items.all()
    
    # Prepare order items string, each item on a new line
    items_str = "\n".join([f"{i+1}. *{item.item_name}* x {item.quantity}" 
                           for i, item in enumerate(order_items)])
    
     # Get the current site domain
    current_site = get_current_site(request)
    domain = current_site.domain
    
    # Generate the order details URL
    order_details_url = f"https://{domain}{reverse('order_success', args=[store_id, order_id])}"

    # Send WhatsApp message to restaurant owner
    business_owner = BusinessOwner.objects.get(store=store)
    params = [
        f"*{store.store_name}*",     # 1st param: Store name (bold)
        str(order.store_order_id),   # 2nd param: Order ID
        order.customer_name,         # 3rd param: Customer name
        order.customer_phone,
        order.get_order_type_display(),
        order.get_payment_method_display(),
        order.get_status_display(),
        str(order.total_price),      # 4th param: Total price
        f"\n{items_str}",
        order_details_url,   # 5th param: Concatenated list of items with "Items:" in bold
    ]


    success = send_whatsapp_message(
        phone=business_owner.phone_number,
        template_name="order_confirmation_request2",
        params=params
    )
    
    if success:
        messages.success(request, "Order confirmation sent to the restaurant.")
    else:
        messages.error(request, "Failed to send order confirmation to the restaurant.")

    return render(request, 'menuimage/order_success.html', {
        'store': store,
        'order': order,
        'order_items': order_items,
    })


@login_required
@require_POST
def confirm_order_payment(request, store_id, order_id):
    store = get_object_or_404(Store, store_id=store_id, owner=request.user)
    order = get_object_or_404(Order, id=order_id, store=store)

    if order.status != 'COMPLETED':
        order.status = 'COMPLETED'
        order.save()
        return JsonResponse({'success': True, 'new_status': 'COMPLETED'})
    else:
        return JsonResponse({'success': False, 'error': 'Order is already completed'}, status=400)

        
@login_required
def my_orders(request, store_id):
    store = get_object_or_404(Store, store_id=store_id, owner=request.user)
    orders = Order.objects.filter(store=store).order_by('-created_at')

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        orders = orders.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query) |
            Q(order_type__icontains=search_query) |
            Q(payment_method__icontains=search_query)
        )

    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    if sort_by in ['created_at', '-created_at', 'total_price', '-total_price', 'customer_name', '-customer_name']:
        orders = orders.order_by(sort_by)

    # Filtering
    order_type = request.GET.get('order_type')
    if order_type:
        orders = orders.filter(order_type=order_type)

    payment_method = request.GET.get('payment_method')
    if payment_method:
        orders = orders.filter(payment_method=payment_method)

    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    # Pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    orders_data = []
    for order in page_obj:
        orders_data.append({
            'id': order.id,
            'store_order_id': order.store_order_id,
            'customer_name': order.customer_name or 'N/A',
            'customer_phone': order.customer_phone or 'N/A',
            'total_price': str(order.total_price),
            'status': order.status,
            'needs_payment_confirmation': order.status == 'PENDING_PAYMENT',
            'order_type': order.order_type or 'N/A',
            'payment_method': order.payment_method,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': [{'name': item.item_name, 'quantity': item.quantity} for item in order.items.all()]
        })

    return JsonResponse({
        'orders': orders_data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })

@login_required
def edit_confirm_view(request, store_id):
    store = get_object_or_404(Store, store_id=store_id)

    if store.owner != request.user:
        return HttpResponseForbidden("You don't have permission to edit this menu.")

    if request.method == 'POST':
        items = request.POST.getlist('items[]')
        prices = request.POST.getlist('prices[]')

        menu_items = []
        for item, price in zip_longest(items, prices, fillvalue=''):
            item = item.strip()
            price = price.strip()
            if item:
                menu_items.append((item, price))

        store.menu_items = menu_items
        store.edited_text = '\n'.join([f"{item} {price}".strip() for item, price in menu_items])
        store.save()

        messages.success(request, 'Menu updated successfully.')
        return redirect('dashboard', store_id=store_id)
    else:
        # If menu_items exists and is not empty, use it. Otherwise, parse edited_text
        if hasattr(store, 'menu_items') and store.menu_items:
            menu_items = store.menu_items
        else:
            # Parse the edited_text to create menu_items
            menu_items = []
            lines = [line.strip() for line in store.edited_text.split('\n') if line.strip()]
            for line in lines:
                match = re.match(r'^(.*?)\s*(\d+(\.\d{1,2})?)$', line)
                if match:
                    item = match.group(1).strip()
                    price = match.group(2)
                    menu_items.append((item, price))
                else:
                    menu_items.append((line, ''))

    return JsonResponse({'menu_items': menu_items})

@login_required
def delete_menu(request, store_id):
    store = get_object_or_404(Store, store_id=store_id)

    if store.owner != request.user:
        return HttpResponseForbidden("You don't have permission to delete this menu.")

    if request.method == 'POST':
        store.delete()
        messages.success(request, 'Menu deleted successfully.')
        return redirect('landing_page')

    return render(request, 'menuimage/new_store.html', {'store': store})

@login_required
def generate_qr(request, store_id):
    store = get_object_or_404(Store, store_id=store_id)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"https://minglemenu.in/{store_id}/")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_png = buffer.getvalue()

    response = HttpResponse(qr_png, content_type="image/png")
    response['Content-Disposition'] = f'attachment; filename="{store.store_name}_qr_code.png"'
    return response


def initiate_payment(request, store_id, order_id):
    store = get_object_or_404(Store, store_id=store_id)
    cart_id = request.session.get(f'cart_id_{store_id}')
    cart_items = CartItem.objects.filter(cart_id=cart_id, store=store)
    total_amount = sum(item.total_price() for item in cart_items)

    order = get_object_or_404(Order, id=order_id, store=store)

    business_owner = BusinessOwner.objects.get(store=store)
    upi_id = business_owner.upi_id

    payment = Payment.objects.create(
        store=store,
        amount=total_amount,
        upi_id=upi_id
    )

    upi_link = f"upi://pay?pa={upi_id}&pn={store.store_name}&am={total_amount}&tn={payment.payment_id}"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_image = buffer.getvalue()

    # Encode the image data as base64
    qr_image_base64 = base64.b64encode(qr_image).decode('utf-8')

    return render(request, 'menuimage/payment.html', {
        'payment': payment,
        'upi_link': upi_link,
        'qr_image': qr_image_base64,
        'cart_items': cart_items,
        'total_amount': total_amount,
        'store': store,
        'order': order,
    })

def confirm_payment(request, store_id, payment_id):
    store = get_object_or_404(Store, store_id=store_id)
    payment = get_object_or_404(Payment, payment_id=payment_id, store=store)
    order = get_object_or_404(Order, store=store, total_price=payment.amount, status='PENDING')

    # Update order status to 'PAYMENT_PENDING'
    order.status = 'PAYMENT_PENDING'
    order.save()

    # Get business owner's phone number
    business_owner = BusinessOwner.objects.get(store=store)
    owner_phone = business_owner.phone_number

    # Prepare WhatsApp message
    items_str = "\n".join([f"{i+1}. *{item.item_name}* x {item.quantity}" 
                           for i, item in enumerate(order.items.all())])

    params = [
        f"*{store.store_name}*",     # Store name
        str(order.store_order_id),   # Order ID
        order.customer_name,         # Customer name
        order.customer_phone,        # Customer phone
        order.get_order_type_display(),  # Order type
        'UPI',                       # Payment method
        'PAYMENT_PENDING',           # Order status
        str(order.total_price),      # Total price
        f"\n{items_str}",            # Order items
    ]

    # Send WhatsApp message
    success = send_whatsapp_message(
        phone=business_owner.phone_number,
        template_name="payment_confirmation_request",
        params=params
    )

    print(params)

    if success:
        return JsonResponse({'status': 'success', 'message': 'Payment confirmation request sent to the restaurant owner.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Failed to send payment confirmation request.'})

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        payment_id = data.get('payment_id')
        status = data.get('status')
        order_data = data.get('order_data', {})

        payment = get_object_or_404(Payment, id=payment_id)
        payment.status = status
        payment.save()

        if status == 'COMPLETED':
            # Create the order here
            store = payment.store
            cart_id = request.session.get(f'cart_id_{store.store_id}')
            cart_items = CartItem.objects.filter(cart_id=cart_id, store=store)

            order = Order.objects.create(
                store=store,
                total_price=payment.amount,
                customer_name=order_data.get('full_name'),
                customer_phone=order_data.get('phone_number'),
                order_type=order_data.get('order_type'),
                payment_method='UPI',
                status='COMPLETED'
            )

            # Add cart items to the order
            order.items.set(cart_items)

            # Clear the cart
            cart_items.delete()
            if f'cart_id_{store.store_id}' in request.session:
                del request.session[f'cart_id_{store.store_id}']

            return JsonResponse({'status': 'success', 'order_id': order.id})

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)

def payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    return JsonResponse({
        'status': payment.status,
        'amount': str(payment.amount),
        'created_at': payment.created_at.isoformat(),
        'updated_at': payment.updated_at.isoformat()
    })


def check_payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return JsonResponse({'status': payment.status})

@csrf_exempt
def whatsapp_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        order_id = data.get('order_id')
        action = data.get('action')  # 'confirm' or 'reject'
        
        try:
            order = Order.objects.get(id=order_id)
            
            if action == 'confirm':
                order.status = 'COMPLETED'
                order.save()
                
                # Clear the cart
                cart_id = f'cart_id_{order.store.store_id}'
                CartItem.objects.filter(cart_id=cart_id, store=order.store).delete()
                
                # Send confirmation message to customer
                send_whatsapp_message(
                    phone=order.customer_phone,
                    template_name="payment_confirmed",
                    params=[order.store.store_name, str(order.store_order_id)]
                )
                
            elif action == 'reject':
                order.status = 'PAYMENT_FAILED'
                order.save()
                
                # Send rejection message to customer
                send_whatsapp_message(
                    phone=order.customer_phone,
                    template_name="payment_rejected",
                    params=[order.store.store_name, str(order.store_order_id)]
                )
            
            return HttpResponse(status=200)
        
        except Order.DoesNotExist:
            return HttpResponse(status=404)
    
    return HttpResponse(status=405)  # Method not allowed

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def manage_store(request, store_id):
    store = get_object_or_404(Store, store_id=store_id, owner=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')
        
        if action in ['create', 'update']:
            form = None
            if item_type == 'offer':
                form = OfferForm(request.POST, instance=Offer.objects.get(id=item_id) if item_id else None)
            elif item_type == 'ad':
                form = AdvertisementForm(request.POST, request.FILES, instance=Advertisement.objects.get(id=item_id) if item_id else None)
            elif item_type == 'coupon':
                form = CouponCodeForm(request.POST, instance=CouponCode.objects.get(id=item_id) if item_id else None)
            
            if form and form.is_valid():
                item = form.save(commit=False)
                item.store = store
                item.save()
                return JsonResponse({'success': True, 'id': item.id})
            else:
                return JsonResponse({'success': False, 'errors': form.errors if form else 'Invalid form'})
        
        elif action == 'delete':
            model = None
            if item_type == 'offer':
                model = Offer
            elif item_type == 'ad':
                model = Advertisement
            elif item_type == 'coupon':
                model = CouponCode
            
            if model:
                model.objects.filter(id=item_id, store=store).delete()
                return JsonResponse({'success': True})
        
        elif action == 'edit':
            model = None
            if item_type == 'offer':
                model = Offer
            elif item_type == 'ad':
                model = Advertisement
            elif item_type == 'coupon':
                model = CouponCode
            
            if model:
                item = model.objects.get(id=item_id, store=store)
                return JsonResponse({'success': True, 'item': model_to_dict(item)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def generate_coupon_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import razorpay
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import CustomUser, SellerProfile, BuyerProfile, StudyMaterial, Purchase, SellerPayout
from .forms import (
    UserLoginForm,
    CustomUserRegistrationForm,
    SellerProfileForm,
    BuyerProfileForm,
    StudyMaterialForm,
)

# Home Page
def home(request):
    materials = StudyMaterial.objects.all().order_by('-uploaded_at')[:4]
    return render(request, 'core/home.html', {
        'materials': materials
    })

def materials(request):
    materials = StudyMaterial.objects.all().order_by('-uploaded_at')
    return render(request, 'core/materials.html', {
        'materials': materials
    })

@csrf_exempt
@login_required
def checkout(request, material_id):
    material = get_object_or_404(StudyMaterial, id=material_id)
    user = request.user

    # If free or already paid, show without Razorpay
    is_already_purchased = (
        material.price == 0 or
        Purchase.objects.filter(buyer=user, material=material, is_paid=True).exists()
    )

    if is_already_purchased:
        return render(request, 'core/checkout.html', {
            'material': material,
            'is_already_purchased': True,
        })

    # Check if pending purchase already exists
    existing_purchase = Purchase.objects.filter(
        buyer=user, material=material, is_paid=False
    ).order_by('-created_at').first()

    if existing_purchase:
        order_id = existing_purchase.razorpay_order_id
    else:
        amount = int(material.price * 100)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))
        order = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1,
            'notes': {
                'buyer_id': str(user.id),
                'material_id': str(material.id),
                'seller_id': str(material.seller.id)
            }
        })

        # Create a new pending purchase
        Purchase.objects.create(
            buyer=user,
            material=material,
            razorpay_order_id=order['id'],
            is_paid=False
        )
        order_id = order['id']

    return render(request, 'core/checkout.html', {
        'order_id': order_id,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': int(material.price * 100),
        'material': material,
        'is_already_purchased': False
    })

# Login (Email or Phone)
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_seller is True:
            return redirect('dashboardSeller')
        elif request.user.is_seller is False:
            return redirect('dashboardBuyer')
        else:
            return redirect('not_verified')

    form = UserLoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.cleaned_data.get('user')
            if user and user.is_active:
                auth_login(request, user)
                if user.is_seller is True:
                    return redirect('dashboardSeller')
                elif user.is_seller is False:
                    return redirect('dashboardBuyer')
                else:
                    return redirect('not_verified')
            else:
                messages.error(request, "Invalid or inactive account.")
        else:
            messages.error(request, "Please correct the errors below.")

    return render(request, 'core/login.html',{'form': form, 'user': request.user})

# Register Seller
def registerSeller(request):
    if request.user.is_authenticated:
        return redirect('dashboardSeller')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            # Avoid duplicate profile creation
            SellerProfile.objects.get_or_create(user=user)

            messages.success(request, "Seller registration successful. You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserRegistrationForm()

    return render(request, 'core/registerSeller.html',{'form': form, 'user': request.user})

# Register Buyer
def registerBuyer(request):
    if request.user.is_authenticated:
        return redirect('dashboardBuyer')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_seller = False
            user.save()

            # Avoid duplicate profile creation
            BuyerProfile.objects.get_or_create(user=user)

            messages.success(request, "Buyer registration successful. You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserRegistrationForm()

    return render(request, 'core/registerBuyer.html',{'form': form, 'user': request.user})

# Seller Dashboard
@login_required
def dashboardSeller(request):
    if not request.user.is_seller:
        return redirect('not_verified')

    try:
        profile = request.user.sellerprofile
        materials = profile.studymaterial_set.all()
    except SellerProfile.DoesNotExist:
        messages.error(request, "Seller profile not found.")
        return redirect('registerSeller')

    now = timezone.now()
    start_of_this_week = now - timedelta(days=now.weekday())  # Monday this week
    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week - timedelta(seconds=1)

    # Paid purchases only, grouped by week
    purchases_this_week = Purchase.objects.filter(
        material__seller=profile,
        is_paid=True,
        created_at__gte=start_of_this_week
    )

    purchases_last_week = Purchase.objects.filter(
        material__seller=profile,
        is_paid=True,
        created_at__range=(start_of_last_week, end_of_last_week)
    )

    # Apply 30% company commission
    def calculate_earnings(purchases):
        commission_rate = Decimal('0.70')
        return sum(p.material.price * commission_rate for p in purchases)


    earnings_this_week = calculate_earnings(purchases_this_week)
    earnings_last_week = calculate_earnings(purchases_last_week)

    # Recent sales: both paid and unpaid
    recent_sales = Purchase.objects.filter(
        material__seller=profile
    ).order_by('-created_at')[:10]

    form = StudyMaterialForm()

    return render(request, 'core/dashboardSeller.html', {
        'profile': profile,
        'materials': materials,
        'form': form,
        'earnings_this_week': earnings_this_week,
        'earnings_last_week': earnings_last_week,
        'sales': recent_sales,
    })

# Buyer Dashboard
@login_required
def dashboardBuyer(request):
    try:
        profile = request.user.buyerprofile
    except BuyerProfile.DoesNotExist:
        messages.error(request, "Buyer profile not found.")
        return redirect('home')
    
    purchases = Purchase.objects.filter(buyer=request.user, is_paid=True).select_related('material').order_by('-created_at')

    return render(request, 'core/dashboardBuyer.html', {
        'profile': profile,
        'user' : request.user,
        'purchases': purchases,
        })

# Upload Study Material (Seller only)
@login_required
def upload(request):
    try:
        profile = request.user.sellerprofile
    except SellerProfile.DoesNotExist:
        messages.error(request, "You must have a seller profile to upload materials.")
        return redirect('registerSeller')

    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.seller = profile
            material.save()
            messages.success(request, "Study material uploaded successfully.")
        else:
            messages.error(request, "Please correct the errors in the form.")
    return redirect('dashboardSeller')

@login_required
def update(request, pk):
    material = get_object_or_404(StudyMaterial, pk=pk, seller=request.user.sellerprofile)

    if request.method == "POST":
        form = StudyMaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            return redirect('dashboardSeller')
    else:
        form = StudyMaterialForm(instance=material)

    return render(request, 'core/dashboardSeller.html', {
        'form': form,
        'material': material
    })

@csrf_exempt
def verify_payment(request):
    data = json.loads(request.body)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })

        purchase = Purchase.objects.get(razorpay_order_id=data['razorpay_order_id'])
        purchase.is_paid=True
        purchase.razorpay_payment_id = data['razorpay_payment_id']
        purchase.included_in_payout = False
        purchase.save()

        return JsonResponse({'status': 'success'})
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'status': 'fail'})

    
def mark_payout_done(seller):
    unpaid = Purchase.objects.filter(
        material__seller=seller,
        is_paid=True,
        included_in_payout=False
    )
    if not unpaid.exists():
        return

    amount = sum(p.material.price for p in unpaid)
    from_date = unpaid.earliest('created_at').created_at
    to_date = unpaid.latest('created_at').created_at

    SellerPayout.objects.create(
        seller=seller,
        amount=amount,
        from_date=from_date,
        to_date=to_date
    )

    unpaid.update(included_in_payout=True)


# Not Verified View
def not_verified(request):
    return render(request, 'core/not_verified.html',{'user': request.user})

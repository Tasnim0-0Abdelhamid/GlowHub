from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, EmailLoginForm, CustomUserUpdateForm
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from .models import Product, Cart, CartItem

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = EmailLoginForm()
    return render(request, 'login.html', {'form': form})


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('profile')
    else:
        form = CustomUserCreationForm() 

    return render(request, 'signup.html', {'form': form})

# -----------------------------------------------

@login_required
def profile_view(request):
    user = request.user
    show_form = False
    show_delete_confirm = False
    form = CustomUserUpdateForm(instance=user)

    if request.method == 'POST' and 'show_edit_form' in request.POST:
        show_form = True
    elif request.method == 'POST' and 'edit_profile' in request.POST:
        if 'edit_profile' in request.POST:
            form = CustomUserUpdateForm(request.POST, instance=user)
            show_form = True
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect('profile')
            
    elif request.method == 'POST' and 'show_delete_confirm' in request.POST:
        show_delete_confirm = True

    elif request.method == 'POST' and 'delete_account' in request.POST:
        user.delete()
        messages.success(request, "Account deleted successfully.")
        return redirect('home')
    
    return render(request, 'profile.html', {
        'user': user,
        'form': form,
        'show_form': show_form,
        'show_delete_confirm': show_delete_confirm 
    })

def home(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    products = Product.objects.all()
    categories = Product.objects.values_list('category', flat=True).distinct()

    if query:
        products = products.filter(name__icontains=query)

    if category and category != 'all':
        products = products.filter(category__iexact=category)

    return render(request, 'home.html', {
        'products': products,
        'categories': categories,
        'selected_category': category or 'all',
        'query': query or '',
    })

def logout_view(request):
    logout(request)
    return redirect('home')

#-------------------------------------------


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += 1
            item.save()
    else:
        cart = request.session.get('cart', {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        request.session['cart'] = cart

    messages.success(request, f"{product.name} added to your cart.", extra_tags='cart')
    return redirect('home')

def cart_view(request):
    items = []
    total = 0

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        for item in cart.items.all():
            items.append({
                'product': item.product,
                'quantity': item.quantity
            })
            total += item.quantity * item.product.price
    else:
        session_cart = request.session.get('cart', {})
        for product_id, quantity in session_cart.items():
            product = get_object_or_404(Product, id=product_id)
            items.append({
                'product': product,
                'quantity': quantity
            })
            total += quantity * product.price

    return render(request, 'cart.html', {'items': items, 'total': total})


def update_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        if request.method == "POST":
            action = request.POST.get('action')
            if action == "increment":
                item.quantity += 1
                item.save()
            elif action == "decrement":
                if item.quantity > 1:
                    item.quantity -= 1
                    item.save()
                else:
                    item.delete()
            elif action == "remove":
                item.delete()
    else:

        session_cart = request.session.get('cart', {})
        if request.method == "POST":
            action = request.POST.get('action')
            pid_str = str(product_id)
            if action == "increment":
                session_cart[pid_str] = session_cart.get(pid_str, 0) + 1
            elif action == "decrement":
                if session_cart.get(pid_str, 0) > 1:
                    session_cart[pid_str] -= 1
                else:
                    session_cart.pop(pid_str, None)
            elif action == "remove":
                session_cart.pop(pid_str, None)
            request.session['cart'] = session_cart

    return redirect('cart')

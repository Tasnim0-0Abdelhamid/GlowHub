from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, EmailLoginForm, CustomUserUpdateForm
from django.contrib import messages
from django.contrib.auth import login, logout
from .models import Product, Cart, CartItem, Order, OrderItem, CustomUser
from django.contrib.admin.views.decorators import staff_member_required

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            session_cart = request.session.get('cart', {})
            if session_cart:
                cart, _ = Cart.objects.get_or_create(user=user)
                for product_id, quantity in session_cart.items():
                    product = Product.objects.get(id=product_id)
                    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                    if not created:
                        item.quantity += quantity
                    else:
                        item.quantity = quantity
                    item.save()
                request.session['cart'] = {}

            return redirect('home')
    else:
        form = EmailLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            session_cart = request.session.get('cart', {})
            if session_cart:
                cart, _ = Cart.objects.get_or_create(user=user)
                for product_id, quantity in session_cart.items():
                    product = Product.objects.get(id=product_id)
                    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                    if not created:
                        item.quantity += quantity
                    else:
                        item.quantity = quantity
                    item.save()
                request.session['cart'] = {}

            messages.success(request, 'Account created successfully.')
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


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
    
    return render(request, 'accounts/profile.html', {
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

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})

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

    return render(request, 'cart-order/cart.html', {'items': items, 'total': total})


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


@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_view') 

    if request.method == "POST":
        address = request.POST.get("address")
        phone = request.POST.get("phone")

        if not address or not phone:
            messages.error(request, "Please fill in all fields.")
            return redirect('checkout')

        order = Order.objects.create(
            user=request.user,
            address=address,
            phone=phone,
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        cart.items.all().delete()

        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_success', order_id=order.id)

    total = sum(item.product.price * item.quantity for item in cart.items.all())
    return render(request, 'cart-order/checkout.html', {'cart': cart, 'total': total})

@login_required
def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    return render(request, 'cart-order/order_success.html', {'order': order})

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-date')
    return render(request, 'accounts/my_orders.html', {'orders': orders})

#------------------------------------------------------------------

@staff_member_required
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    in_transit_orders = Order.objects.filter(status='in_transit').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    completed_orders = Order.objects.filter(status='completed').count()

    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'in_transit_orders': in_transit_orders,
        'delivered_orders': delivered_orders,
        'completed_orders': completed_orders,
    }
    return render(request, 'admin/admin_dashboard.html', context)

@staff_member_required
def manage_products(request):
    products = Product.objects.all()
    query = request.GET.get('q', '')
    if query:
        products = products.filter(name__icontains=query)  # فلترة حسب الاسم
    categories = Product.objects.values_list('category', flat=True).distinct()
    selected_category = request.GET.get('category', 'all')
    if selected_category != 'all':
        products = products.filter(category__iexact=selected_category)
    context = {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': selected_category,
    }
    return render(request, 'admin/manage_products.html', context)

@staff_member_required
def add_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")
        description = request.POST.get("description")
        price = request.POST.get("price")
        stock = request.POST.get("stock_quantity")
        image = request.FILES.get("image")

        Product.objects.create(
            name=name,
            category=category,
            description=description,
            price=price,
            stock_quantity=stock,
            image=image
        )
        messages.success(request, "Product added successfully!")
        return redirect('manage_products')

    return render(request, 'admin/add_product.html')


@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.category = request.POST.get("category")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.stock_quantity = request.POST.get("stock_quantity")
        image = request.FILES.get("image")
        if image: 
            product.image = image

        product.save()
        messages.success(request, "Product updated successfully!")
        return redirect('manage_products')

    return render(request, 'admin/edit_product.html', {'product': product})


@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('manage_products')

@staff_member_required
def manage_orders(request):
    orders = Order.objects.all().select_related('user')
    query = request.GET.get('q', '')
    if query:
        orders = orders.filter(id__icontains=query)
    
    status_choices = [choice[0] for choice in Order.STATUS_CHOICES] 
    selected_status = request.GET.get('status', 'all')
    if selected_status != 'all':
        orders = orders.filter(status=selected_status)

    context = {
        'orders': orders,
        'query': query,
        'status': status_choices,
        'selected_status': selected_status,
    }

    return render(request, 'admin/manage_orders.html', context)

@staff_member_required
def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.status = request.POST.get("status")
        order.save()
        messages.success(request, "Order updated successfully!")
        return redirect('manage_orders')

    return render(request, 'admin/edit_order.html', {'order': order})

@staff_member_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, "Order deleted successfully!")
    return redirect('manage_orders')
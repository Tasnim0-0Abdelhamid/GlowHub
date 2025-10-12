from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, EmailLoginForm, CustomUserUpdateForm
from django.contrib import messages
from django.contrib.auth import login, logout
from .models import Product

# Create your views here.


def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products}) 

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
    
    return render(request, 'profile.html', {
        'user': user,
        'form': form,
        'show_form': show_form
    })

def logout_view(request):
    logout(request)
    return redirect('home')

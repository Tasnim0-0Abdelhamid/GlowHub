from django.contrib import admin
from .models import CustomUser, Product, Order, Cart, CartItem
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(CartItem)
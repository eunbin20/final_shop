from django.shortcuts import render, get_object_or_404
from .models import *
from cart.forms import AddProductForm
from cart.cart import Cart

def product_in_category(request, category_slug=None):
    # 맥락변수 3종을 목록 화면으로 전달
    current_category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available_display=True)
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=current_category)
    cart = Cart(request)
    return render(request, 'shop/list.html',
                  {'current_category': current_category, # 지정된 카테고리 객체
                   'categories': categories,             # 모든 카테고리 객체
                   'products': products,
                   'cart': cart
                   })                # 모든 또는 지정된 카테고리의 상품


def product_detail(request, id, product_slug=None):
    # 지정된 상품 객체를 상세 화면으로 전달
    product = get_object_or_404(Product, id=id, slug=product_slug)
    add_to_cart = AddProductForm(initial={'quantity': 1})
    cart = Cart(request)
    return render(request, 'shop/detail.html', {'product': product,
                                                'add_to_cart': add_to_cart,
                                                'cart': cart})  # !!!


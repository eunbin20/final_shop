from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from shop.models import Product
from .forms import AddProductForm
from .cart import Cart
from coupon.forms import AddCouponForm

@require_POST
def add(request, product_id):  # 장바구니에 상품을 추가하는 뷰
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = AddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd['quantity'], is_update=cd['is_update'])
    return redirect('cart:detail')


def remove(request, product_id):  # 장바구니에서 지정한 상품을 삭제하는 뷰
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:detail')


def detail(request):  # 장바구니 페이지 뷰
    cart = Cart(request)
    add_coupon = AddCouponForm()  # !!! AddCouponForm
    for product in cart:  # 장바구니에 담긴 상품마다 (수량 수정 가능하도록) AddProductForm 생성
        product['quantity_form'] = AddProductForm(
            initial={'quantity': product['quantity'], 'is_update': True}
        )
    return render(request, 'cart/detail.html', {'cart': cart, 'add_coupon': add_coupon})



from .cart import Cart

def cart(request):
    cart = Cart(request)
    return {'cart':cart}  # 장바구니 정보를 사전형으로 반환

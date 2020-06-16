from decimal import Decimal
from django.conf import settings
from shop.models import Product
from coupon.models import Coupon


class Cart(object):
    def __init__(self, request):
        # 장바구니 초기화 메소드 (request.session 변수에 저장)
        self.session = request.session
        cart = self.session.get(settings.CART_ID)  # CART_ID 변수는 settings.py 파일에서 정의
        if not cart:
            cart = self.session[settings.CART_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')  # 카트에 쿠폰 id 변수 추가


    def __len__(self):
        # 장바구니의 상품별 수량에 대한 총계
        return sum(
            item['quantity'] for item in self.cart.values()
        )

    def __iter__(self):
        # 장바구니에 담긴 상품의 가격과 금액을 iterable 상태로 제공하는 메소드
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            self.cart[str(product.id)]['product'] = product
        for item in self.cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item  # https://tech.ssut.me/what-does-the-yield-keyword-do-in-python/

    def add(self, product, quantity=1, is_update=False):
        # 장바구니에 상품 추가
        product_id = str(product.id)
        if product_id not in self.cart:
            # 일단 수량을 0으로 초기화
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        if is_update:  # 지정한 수량으로 수정
            self.cart[product_id]['quantity'] = quantity
        else:          # 지정한 만큼 수량 증가
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        # 장바구니에 담긴 상품을 세션 변수로 저장
        self.session[settings.CART_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        # 장바구니에서 특정 상품을 삭제
        product_id = str(product.id)
        if product_id in self.cart:
            del(self.cart[product_id])
            self.save()

    def clear(self):
        # 장바구니를 비우는 기능, 주문 완료 경우에도 사용
        self.session[settings.CART_ID] = {}
        self.session['coupon_id'] = None # 장바구니 비울 때, 쿠폰 정보도 삭제
        self.session.modified = True

    def get_product_total(self):
        # 장바구니에 담긴 상품의 총 가격을 계산
        return sum(
            Decimal(item['price']) * item['quantity'] for item in self.cart.values()
        )

    @property  # 클래스 메소드를 클래스 속성 변수로 만들기 위하여
    def coupon(self):
        if self.coupon_id:
            return Coupon.objects.get(id=self.coupon_id)
        return None

    def get_discount_total(self):
        if self.coupon:
            if self.get_product_total() >= self.coupon.amount:
                return self.coupon.amount
        return Decimal(0)  # (구매총액 < 쿠폰금액)이면 할인금액은 0

    def get_total_price(self):  # 할인 적용된 촘 금액 반환
        return self.get_product_total() - self.get_discount_total()

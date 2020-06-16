from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from django.db.models.signals import post_save
import hashlib
from .iamport import payments_prepare, find_transaction
from coupon.models import Coupon

from shop.models import Product



class Order(models.Model):  # Order:OrderItem = 일:다
    # 주문 정보를 저장하는 모델 (회원 정보를 외래키로 연결하지 않고, 저장하는 방식)
    first_name = models.CharField(max_length=50)        # 주문자 정보
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)          # 주소
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)   # 일시
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)           # 결제 여부

    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name='order_coupon', null=True, blank=True)
    discount = models.IntegerField(default=0, validators=[MinValueValidator(0),MaxValueValidator(100000)])

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return 'Order {}'.format(self.id)

    def get_total_product(self):  # (할인 전) 주문 총액(=단가*수량)
        return sum(
            item.get_item_price() for item in self.items.all())  # 자식 테이블에서 지정한 related_name

    def get_total_price(self):  # (할인 후) 주문 총액
        total_product = self.get_total_product()
        return total_product - self.discount


class OrderItem(models.Model):  # Order:OrderItem = 일:다, OrderItem:Product = 다:일
    # 주문 내역 정보
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_products')
    price = models.DecimalField(max_digits=10, decimal_places=2)  # 상품 테이블 단가와 별도로 저장
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return '{}'.format(self.id)

    def get_item_price(self):
        return self.price * self.quantity


class OrderTransactionManager(models.Manager):
    # OrderTransaction 모델의 관리자 클래스, 기본 관리자 클래스 objects 대신 사용
    def create_new(self, order, amount, success=None, transaction_status=None):
        if not order:
            raise ValueError("주문 오류")

        order_hash = hashlib.sha1(str(order.id).encode('utf-8')).hexdigest()
        email_hash = str(order.email).split("@")[0]
        final_hash = hashlib.sha1((order_hash  + email_hash).encode('utf-8')).hexdigest()[:10]
        merchant_order_id = "%s"%(final_hash)  # 아임포트에 결제 요청할 때 고유한 주문번호가 요구됨
        payments_prepare(merchant_order_id,amount)

        tranasction = self.model(
            order=order,
            merchant_order_id=merchant_order_id,
            amount=amount
        )

        if success is not None:
            tranasction.success = success
            tranasction.transaction_status = transaction_status

        try:
            tranasction.save()
        except Exception as e:
            print("save error",e)

        return tranasction.merchant_order_id

    def get_transaction(self, merchant_order_id):
        result = find_transaction(merchant_order_id)
        if result['status'] == 'paid':
            return result
        else:
            return None


class OrderTransaction(models.Model):
    # 결제 정보를 저장하는 모델
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    merchant_order_id = models.CharField(max_length=120, null=True, blank=True)
    transaction_id = models.CharField(max_length=120, null=True, blank=True)  # 정산 문제 확인 및 환불 처리 용도
    amount = models.PositiveIntegerField(default=0)
    transaction_status = models.CharField(max_length=220, null=True,blank=True)
    type = models.CharField(max_length=120, blank=True)
    created = models.DateTimeField(auto_now_add=True, auto_now=False)

    objects = OrderTransactionManager()  # 기본 관리자 클래스를 자작 관리자 클래스로 지정

    def __str__(self):
        return str(self.order.id)

    class Meta:
        ordering = ['-created']


def order_payment_validation(sender, instance, created, *args, **kwargs):
    # (특정 기능의 수행을 장고 앱 전체에 알리는) 시그널을 활용한 결제 검증 함수
    if instance.transaction_id:
        import_transaction = OrderTransaction.objects.get_transaction(merchant_order_id=instance.merchant_order_id)

        merchant_order_id = import_transaction['merchant_order_id']
        imp_id = import_transaction['imp_id']
        amount = import_transaction['amount']

        local_transaction = OrderTransaction.objects.filter(
            merchant_order_id=merchant_order_id, transaction_id= imp_id, amount=amount).exists()

        if not import_transaction or not local_transaction:
            raise ValueError("비정상 거래입니다.")

# 결제 정보가 생성된 후에 호출할 함수를 연결해준다.
post_save.connect(order_payment_validation, sender=OrderTransaction)
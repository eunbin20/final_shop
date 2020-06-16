from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View  # 결제를 위한 임포트
from django.http import JsonResponse        # 결제를 위한 임포트

from .models import *
from cart.cart import Cart
from .forms import *



def order_create(request):
    # 주문 입력 뷰, 결제 진행 후 주문 정보를 저장,
    # ajax 기능으로 주문서 처리하므로 주문서 입력용 폼 출력하는 경우를 제외하면,
    # 자바스크립트가 동작하지 않는 환경에서만 입력 정보를 처리하는 뷰
    cart = Cart(request)
    if request.method == 'POST':  # 서버로 정보가 전달되면
        form = OrderCreateForm(request.POST)  # 주문서 입력 폼 저장
        if form.is_valid():
            order = form.save()  # 폼을 저장
            if cart.coupon:  # 카트에 쿠폰이 있으면, 주문에 적용
                order.coupon = cart.coupon
                order.discount = cart.coupon.amount
                order.save()
            for item in cart:  # 카트의 모든 상품을 주문내역으로 생성
                OrderItem.objects.create(
                    order=order, product=item['product'], price=item['price'], quantity=item['quantity'])
            cart.clear()  # 카트 비우기
            return render(request, 'order/created.html', {'order': order})  # 저장된 주문 정보를 맥락 정보로 전달
    else:  # 사용자가 정보를 서버로 전달하지 않은 상태라면
        form = OrderCreateForm()  # 주문서 입력 폼 생성하고, 카트 및 폼을 템플릿으로 전달
    return render(request, 'order/create.html', {'cart': cart, 'form': form})


from django.contrib.admin.views.decorators import staff_member_required
@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order/admin/detail.html', {'order':order})

# pdf를 위한 임포트
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint

@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('order/admin/pdf.html', {'order':order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename=order_{}.pdf'.format(order.id)
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATICFILES_DIRS[0]+'/css/pdf.css')])
    return response


def order_complete(request):
    # ajax로 결제 후에 보여줄 결제 완료 화면
    order_id = request.GET.get('order_id')  # 서버로부터 주문번호를 얻어와서
    order = Order.objects.get(id=order_id)  # 이 주문번호를 이용해서 주문 완료 화면을 출력
    return render(request, 'order/created.html', {'order': order})


class OrderCreateAjaxView(View):  # Ajax 뷰
    # 입력된 주문 정보를 서버에 저장하고, 카트 상품을 OrderItem 객체에 저장하고, 카트 비우기
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:  # 인증되지 않은 사용자라면 403 상태 반환
            return JsonResponse({"authenticated": False}, status=403)

        cart = Cart(request)                    # 카트 정보 획득
        form = OrderCreateForm(request.POST)    # 입력된 주문 정보 획득

        if form.is_valid():  # 폼이 정당하면
            order = form.save(commit=False)  # 폼을 메모리에서 저장
            if cart.coupon:                  # 쿠폰 정보 처리
                order.coupon = cart.coupon
                order.discount = cart.coupon.amount
            order = form.save()             # 폼 저장
            for item in cart:               # 카트를 OrderItem으로 저장
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])
            cart.clear()                    # 카트 비우기
            data = {"order_id": order.id}
            return JsonResponse(data)       # 주문번호를 반환
        else:   # 폼이 정당하지 않으면 401 상태 반환
            return JsonResponse({}, status=401)


class OrderCheckoutAjaxView(View):  # 결제 정보 OrderTransaction 객체 생성
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:  # 인증되지 않은 사용자이면 403 상태 반환
            return JsonResponse({"authenticated":False}, status=403)

        order_id = request.POST.get('order_id')  # 입력된 주문번호 획득하여 주문 검색
        order = Order.objects.get(id=order_id)
        amount = request.POST.get('amount')      # 입력된 금액 획득

        try:  # 결제용 id 생성을 시도
            merchant_order_id = OrderTransaction.objects.create_new(
                order=order, amount=amount)
        except:  # 결제용 id 생성 실패한 경우
            merchant_order_id = None

        if merchant_order_id is not None:  # 결제용 id 생성이 성공한 경우
            data = {"works": True, "merchant_id": merchant_order_id}
            return JsonResponse(data)
        else:  # 결제용 id 생성이 실패한 경우 401 상태 반환
            return JsonResponse({}, status=401)


class OrderImpAjaxView(View):  # 실제 결제 여부 확인
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:  # 사용자 인증 실패이면 403 반환
            return JsonResponse({"authenticated": False}, status=403)
        order_id = request.POST.get('order_id')  # 주문번호 획득
        order = Order.objects.get(id=order_id)
        merchant_id = request.POST.get('merchant_id')  # 결제번호 획득
        imp_id = request.POST.get('imp_id')
        amount = request.POST.get('amount')
        try:  # 결제 객체 검색 시도
            trans = OrderTransaction.objects.get(
                order=order, merchant_order_id=merchant_id, amount=amount)
        except:
            trans = None

        if trans is not None:  # 결제 객체 검색 성공이면
            trans.transaction_id = imp_id
            trans.success = True
            trans.save()
            order.paid = True
            order.save()

            data = {
                "works": True
            }

            return JsonResponse(data)
        else:  # 결제 객체 검색 실패하면 401 반환
            return JsonResponse({}, status=401)
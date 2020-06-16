from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Coupon
from .forms import AddCouponForm


@require_POST
def add_coupon(request):  # 입력받은 쿠폰 코드로 쿠폰을 조회
    now = timezone.now()
    form = AddCouponForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['code']
        try:
            coupon = Coupon.objects.get(  # iexact로 대소문자 구분 없이
                code__iexact=code,        # use_from <= now <= use_to
                use_from__lte=now, use_to__gte=now, active=True)  # active=True
            request.session['coupon_id'] = coupon.id  # 쿠폰 id를 세션 변수로 저장
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
    return redirect('cart:detail')  # 장바구니 보기로 리다이렉트
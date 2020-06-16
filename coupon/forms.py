from django import forms


class AddCouponForm(forms.Form):  # 쿠폰 번호 입력하는 폼
    code = forms.CharField(label='Your Coupon Code')
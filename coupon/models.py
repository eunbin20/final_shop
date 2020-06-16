from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)  # 쿠폰 사용할 때 입력할 코드
    use_from = models.DateTimeField()                    # 쿠폰 사용 시작 시점
    use_to = models.DateTimeField()                      # 쿠폰 사용 종료 시점
    amount = models.IntegerField(                        # 할인 금액 (최대/최소 제약)
        validators=[MinValueValidator(0), MaxValueValidator(100000)])
    active = models.BooleanField()						 # True인 쿠폰만 유효함

    def __str__(self):
        return self.code

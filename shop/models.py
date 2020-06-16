from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)  # 카테고리 이름, DB 색인 열로 지정
    meta_description = models.TextField(blank=True)         # SEO(검색 엔진 최적화)를 위한 열 https://support.google.com/webmasters/answer/7451184?hl=ko

    slug = models.SlugField(max_length=200, db_index=True, unique=True,
		allow_unicode=True)  # 카테고리 및 상품 이름으로 URL 만들기, 유니코드 허용

    class Meta:
        ordering = ['name']
        verbose_name = 'category'           # 관리자 페이지 용
        verbose_name_plural = 'categories'  # 관리자 페이지 용

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_in_category', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
		null=True, related_name='products')  # 외래키, 부모 삭제 시 널 지정
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, db_index=True, unique=True, allow_unicode=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    description = models.TextField(blank=True)
    meta_description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # 가격, 소수점
    stock = models.PositiveIntegerField()                         # 재고, 음수 불허
    available_display = models.BooleanField('Display', default=True)    # 상품 노출 여부
    available_order = models.BooleanField('Order', default=True)        # 상품 주문 가능 여부
    created = models.DateTimeField(auto_now_add=True)       # settings.USE_TZ = False
    updated = models.DateTimeField(auto_now=True)           # settings.USE_TZ = False

    class Meta:
        ordering = ['-created']
        index_together = [['id','slug']]    # 다중 열 색인

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])
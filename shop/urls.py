from django.urls import path
from .views import *

app_name = 'shop'

urlpatterns = [
    path('', product_in_category,
         name='product_all'),  		# 카테고리 지정 없이, 모든 상품을 조회
    # path('<slug:category_slug>/', product_in_category, # !!! 한글 슬러그 문제
    #      name='product_in_category'), # 카테고리 지정하여, 해당 상품을 조회
    path('<category_slug>/', product_in_category,
         name='product_in_category'),   # 카테고리 지정하여, 해당 상품을 조회
    path('<int:id>/<product_slug>/', product_detail,
         name='product_detail'),        # 상품 지정하여, 해당 상품을 조회
]

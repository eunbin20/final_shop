from django.contrib import admin
from .models import *


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}  # slug 열을 name 열 값으로 자동 설정


admin.site.register(Category, CategoryAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'price', 'stock',
                    'available_display', 'available_order', 'created', 'updated']
    list_filter = ['available_display', 'created', 'updated', 'category']
    prepopulated_fields = {'slug': ('name',)}  # slug 열을 name 열 값으로 자동 설정
    list_editable = ['price', 'stock', 'available_display', 'available_order']  # 목록에서도 주요 값 수정 허용


admin.site.register(Product, ProductAdmin)
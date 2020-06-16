import csv
import datetime
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import admin

from .models import OrderItem, Order


def export_to_csv(modeladmin, request, queryset):   # 주문 목록을 csv로 저장하는 함수
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    # HttpResponse 객체로 응답을 만들 때, 'Content-Disposition' 값을 attachment 형식으로 설정하면
    # 브라우저가 이 응답을 파일로 다운로드해 줌
    response['Content-Disposition'] = 'attachment;filename={}.csv'.format(opts.verbose_name)
    writer = csv.writer(response)
    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
    # csv 파일 컬럼 타이틀 줄
    writer.writerow([field.verbose_name for field in fields])
    # 실제 데이터 출력
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime("%Y-%m-%d")
            data_row.append(value)
        writer.writerow(data_row)
    return response


def order_detail(obj):  # 주문 목록에 열 데이터로 출력되는 값을 뷰를 호출하여 HTML 태그로 생성
    return mark_safe('<a href="{}">Detail</a>'.format(reverse('orders:admin_order_detail', args=[obj.id])))


def order_pdf(obj):  # 주문 목록에 열 데이터로 출력되는 값을 뷰를 호출하여 HTML 태그로 생성
    return mark_safe('<a href="{}">PDF</a>'.format(reverse('orders:admin_order_pdf', args=[obj.id])))


class OrderItemInline(admin.TabularInline):  # TabularInline 상속, 주문 정보 아래에 주문 내역 출력
    model = OrderItem
    raw_id_fields = ['product']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','first_name','last_name','email','address','postal_code','city','paid',order_detail, order_pdf,'created','updated']
    list_filter = ['paid','created','updated']
    inlines = [OrderItemInline]  # 다른 모델과 연결되어있는 경우 한페이지 표시하고 싶을 때
    actions = [export_to_csv]


# 해당 함수를 관리자 페이지에 명령으로 추가할 때 사용할 이름 지정
export_to_csv.short_description = 'Export to CSV'
order_detail.short_description = 'Detail'
order_pdf.short_description = 'PDF'

admin.site.register(Order, OrderAdmin)
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='menuimage/login.html'), name='login'),
    path('image_recognition/', views.image_recognition_view, name='image_recognition_view'),
    path('create_menu/', views.manual_menu_creation_view, name='create_manual_menu'),
    path('<str:store_id>/dashboard/', views.dashboard_view, name='dashboard'),
    path('<str:store_id>/', views.store_page_view, name='store_page'),  
    path('edit/<str:store_id>/', views.edit_confirm_view, name='edit_confirm_page'),
    path('delete/<str:store_id>/', views.delete_menu, name='delete_menu'),
    path('generate_qr/<str:store_id>/', views.generate_qr, name='generate_qr'),
    path('<str:store_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('<str:store_id>/cart/', views.view_cart, name='view_cart'),
    path('<str:store_id>/update-cart/', views.update_cart, name='update_cart'),
    path('<str:store_id>/place-order/', views.place_order, name='place_order'),
    path('<str:store_id>/business-info/', views.business_info_view, name='business_info'),
    path('<str:store_id>/initiate-payment/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('payment-status/<uuid:payment_id>/', views.payment_status, name='payment_status'),
    path('check-payment-status/<uuid:payment_id>/', views.check_payment_status, name='check_payment_status'),
    path('<str:store_id>/fix_menu/', views.fix_menu, name='fix_menu'),
    path('manage-store/<str:store_id>/', views.manage_store, name='manage_store'),
    path('<str:store_id>/my-orders/', views.my_orders, name='my_orders'),
    path('confirm_payment/<str:store_id>/<uuid:payment_id>/', views.confirm_payment, name='confirm_payment'),
    path('<str:store_id>/order_success/<int:order_id>/', views.order_success, name='order_success'),
    path('<str:store_id>/order/<int:order_id>/confirm-payment/', views.confirm_order_payment, name='confirm_order_payment'),
    path('whatsapp-callback/', views.whatsapp_callback, name='whatsapp_callback'),


]
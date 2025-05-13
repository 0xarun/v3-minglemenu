# forms.py
from django import forms
from django_ckeditor_5.fields import CKEditor5Field
from .models import Store, BusinessOwner, Offer, Advertisement, CouponCode
from django.forms import formset_factory


class StoreForm(forms.ModelForm):
    edited_text = CKEditor5Field('Menu Items', config_name='extends')

    class Meta:
        model = Store
        fields = ['store_name', 'edited_text']
        widgets = {
            'store_name': forms.TextInput(attrs={'placeholder': 'Enter the store name', 'class': 'rectangle-1'}),
        }

class BusinessOwnerForm(forms.ModelForm):
    class Meta:
        model = BusinessOwner
        fields = ['first_name', 'last_name', 'phone_number', 'upi_id']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'rectangle-1'}),
            'last_name': forms.TextInput(attrs={'class': 'rectangle-1'}),
            'phone_number': forms.TextInput(attrs={'class': 'rectangle-1'}),
            'upi_id': forms.TextInput(attrs={'class': 'rectangle-1'}),
        }


class MenuItemForm(forms.Form):
    store_name = forms.CharField(
        label='Store Name', 
        max_length=100, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter the store name', 'class': 'rectangle-1'})
    )

class ItemPriceForm(forms.Form):
    item_name = forms.CharField(
        label='Item Name',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter item name', 'class': 'rectangle-2-item'})
    )
    item_price = forms.DecimalField(
        label='Price',
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter price', 'class': 'rectangle-2-price'})
    )

ItemPriceFormSet = formset_factory(ItemPriceForm, extra=1)

class EditTextForm(forms.Form):
    edited_text = CKEditor5Field('Menu Items', config_name='extends')


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['title', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['title', 'content', 'image', 'is_active']

class CouponCodeForm(forms.ModelForm):
    class Meta:
        model = CouponCode
        fields = ['code', 'discount_percentage', 'is_active', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
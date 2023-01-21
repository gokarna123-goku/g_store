from django import forms
from .models import Customer, Order
from django.contrib.auth.models import User


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_by', 'shipping_address', 'mobile', 'email', 'payment_method']

class RegistrationForm(forms.ModelForm): 
    username = forms.CharField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '@goku', 'style': 'border-radius: 0px;'}))
    password = forms.CharField(widget=forms.PasswordInput())
    email = forms.CharField(widget=forms.EmailInput())
    class Meta:
        model = Customer
        fields = ['fullname', 'email', 'address', 'username', 'password']
    
    def clean_username(self):
        uname = self.cleaned_data.get("username")
        if User.objects.filter(username=uname).exists():
            raise forms.ValidationError("User with this username already exists.")
        return uname
    
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())

    
# class AdminLoginForm(forms.Form):
#     username = forms.CharField(widget=forms.TextInput())
#     password = forms.CharField(widget=forms.PasswordInput())


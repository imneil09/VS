from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, SellerProfile, BuyerProfile, StudyMaterial, Purchase, SellerPayout, SupportTicket
from django.contrib.auth import authenticate
from django.db.models import Q

class CustomUserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone', 'password1', 'password2', 'is_seller']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if user.is_seller:
                SellerProfile.objects.create(user=user)
            else:
                BuyerProfile.objects.create(user=user)
        return user


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ['expertise', 'qualification', 'experience', 'bio']


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = BuyerProfile
        fields = ['interests']


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['title', 'description', 'file', 'banner', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'banner': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['buyer', 'material', 'razorpay_order_id', 'razorpay_payment_id', 'is_paid', 'included_in_payout']


class SellerPayoutForm(forms.ModelForm):
    class Meta:
        model = SellerPayout
        fields = ['seller', 'amount', 'from_date', 'to_date']


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['user', 'subject', 'message', 'is_resolved']


class UserLoginForm(forms.Form):
    email_or_phone = forms.CharField(label="Email or Phone", max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('email_or_phone')
        password = cleaned_data.get('password')

        if identifier and password:
            try:
                users = CustomUser.objects.filter(Q(email=identifier) | Q(phone=identifier))

                if users.count() > 1:
                    raise forms.ValidationError("Multiple accounts found. Please contact support.")

                user_obj = users.first()
                if not user_obj:
                    raise forms.ValidationError("Invalid login credentials")

                user = None
                if user_obj.email:
                    user = authenticate(username=user_obj.email, password=password)
                else:
                    # You need a custom backend to support phone login
                    raise forms.ValidationError("Login by phone not supported currently.")

                if user is None:
                    raise forms.ValidationError("Invalid login credentials")

                cleaned_data['user'] = user

            except CustomUser.MultipleObjectsReturned:
                raise forms.ValidationError("Multiple accounts found. Please contact support.")

        return cleaned_data

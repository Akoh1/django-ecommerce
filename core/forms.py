from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


CHOICES_OF_PAYEMNT = (
	('P', 'PayPal'),
	('S', 'Stripe')
	)

class CheckoutOrderForm(forms.Form):
	country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(
		attrs={
		'class': 'custom-select d-block w-100'
		}))
	street = forms.CharField(widget=forms.TextInput(
		attrs={'placeholder': '1234 Main St'}))
	apartment = forms.CharField(required=False, widget=forms.TextInput(
		attrs={'placeholder': 'Apartment or suite'}))
	zip_code = forms.CharField(widget=forms.TextInput(attrs={
		'class': 'custom-select d-block w-100'
		}))
	save_information = forms.BooleanField(required=False)
	same_billing_address = forms.BooleanField(required=False)
	payment = forms.ChoiceField(widget=forms.RadioSelect(), 
		choices=CHOICES_OF_PAYEMNT)
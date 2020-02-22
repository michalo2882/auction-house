from django import forms


class CreateListingForm(forms.Form):
    count = forms.IntegerField(label='Count')
    price = forms.IntegerField(label='Price')


class BuyForm(forms.Form):
    count = forms.IntegerField(label='Count')

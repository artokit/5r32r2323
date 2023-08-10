from django import forms


class SendForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea(attrs={'class': 'message-text', 'placeholder': 'Введите текст'}))
    photo = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'message-photo', 'title': '1', 'onChange': 'loadPhoto(this)'}),
        required=False
    )

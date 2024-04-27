from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    last_name=forms.CharField(max_length=100,required=True)
    first_name=forms.CharField(max_length=100,required=True)
    email=forms.EmailField(max_length=250,help_text='example@email.com')
    
    class Meta:
        model=User
        fields={'last_name','first_name','username','email'}
        


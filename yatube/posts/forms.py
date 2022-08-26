from .models import Post
from django import forms


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа')
        }
        help_texts = {
            "text": ('Текст нового поста'),
            "group": ('Группа, к которой будет относиться пост'),
        }

from django import forms

from .models import Comment, Post, Report


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

    class Meta:
        model = Post
        fields = ("content", "image", "audience", "comments_enabled")
        widgets = {"content": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("content", "").strip() and not cleaned_data.get("image"):
            raise forms.ValidationError("Write something or add an image to post.")
        return cleaned_data


class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content"].widget.attrs["class"] = "form-control"

    class Meta:
        model = Comment
        fields = ("content",)
        widgets = {"content": forms.TextInput(attrs={"placeholder": "Write a comment..."})}


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ("reason",)
        widgets = {"reason": forms.Textarea(attrs={"rows": 3})}
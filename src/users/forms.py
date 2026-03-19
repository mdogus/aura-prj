from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserCreationForm

from .models import User


def apply_common_field_attrs(field, name, *, placeholder=None, autocomplete=None):
    field.widget.attrs.setdefault("class", "input-field")
    field.widget.attrs.setdefault("aria-required", "true" if field.required else "false")
    if placeholder:
        field.widget.attrs.setdefault("placeholder", placeholder)
    if autocomplete:
        field.widget.attrs.setdefault("autocomplete", autocomplete)
    if field.help_text:
        field.widget.attrs.setdefault("aria-describedby", f"id_{name}_help")
    if isinstance(field.widget, forms.Textarea):
        field.widget.attrs.setdefault("spellcheck", "true")


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "username": "Kullanıcı adı",
            "email": "E-posta adresi",
            "first_name": "Ad",
            "last_name": "Soyad",
            "role": "Rol",
            "password1": "Şifre",
            "password2": "Şifre (tekrar)",
        }
        help_texts = {
            "username": "Giriş yaparken kullanacağınız benzersiz ad.",
            "password1": "Şifreniz en az 8 karakter olmalı ve kolay tahmin edilmemeli.",
            "password2": "Doğrulama için aynı şifreyi tekrar girin.",
        }
        placeholders = {
            "username": "kullanici_adi",
            "email": "ornek@universite.edu.tr",
            "first_name": "Adınız",
            "last_name": "Soyadınız",
        }
        autocomplete_map = {
            "username": "username",
            "email": "email",
            "first_name": "given-name",
            "last_name": "family-name",
            "password1": "new-password",
            "password2": "new-password",
        }
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            if name in help_texts:
                field.help_text = help_texts[name]
            apply_common_field_attrs(
                field,
                name,
                placeholder=placeholders.get(name),
                autocomplete=autocomplete_map.get(name),
            )
        self.fields["username"].widget.attrs.setdefault("autofocus", "autofocus")


class ProfileOnboardingForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "university",
            "department",
            "preferred_communication",
            "accessibility_needs",
            "support_topics",
            "availability_notes",
        )
        widgets = {
            "accessibility_needs": forms.Textarea(attrs={"rows": 4}),
            "support_topics": forms.Textarea(attrs={"rows": 4}),
            "availability_notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "university": "Üniversite",
            "department": "Bölüm",
            "preferred_communication": "Tercih edilen iletişim biçimi",
            "accessibility_needs": "Erişilebilirlik notları",
            "support_topics": "Destek alanları",
            "availability_notes": "Uygunluk notları",
        }
        placeholders = {
            "university": "Üniversite adını yazın",
            "department": "Bölüm veya program adını yazın",
            "preferred_communication": "Örneğin: platform mesajları, e-posta",
            "accessibility_needs": "Varsa ekran okuyucu, dosya biçimi veya iletişim ihtiyaçlarınızı yazın.",
            "support_topics": "Dersler, konular veya destek başlıklarını yazın.",
            "availability_notes": "Uygun olduğunuz gün ve saat aralıklarını yazın.",
        }
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            apply_common_field_attrs(field, name, placeholder=placeholders.get(name))

        role = self.instance.role
        if role == User.Roles.VISUALLY_IMPAIRED_STUDENT:
            self.fields["support_topics"].help_text = (
                "Paylaşılacak dersleri, konuları veya destek beklentilerinizi belirtin."
            )
        elif role == User.Roles.VOLUNTEER_STUDENT:
            self.fields["accessibility_needs"].help_text = (
                "Varsa iletişim ve destek sunumu için özel notlarınızı ekleyin."
            )
        elif role == User.Roles.ACADEMIC_ADVISOR:
            self.fields["support_topics"].help_text = (
                "Destek verebileceğiniz dersleri, alanları veya akademik uzmanlıkları yazın."
            )
            self.fields["availability_notes"].help_text = (
                "Öğrencilerle çalışmak için uygun olduğunuz zaman aralıklarını yazın."
            )
        else:
            self.fields["accessibility_needs"].required = False
            self.fields["support_topics"].required = False
            self.fields["availability_notes"].required = False

        for name, field in self.fields.items():
            if field.help_text:
                field.widget.attrs["aria-describedby"] = f"id_{name}_help"
            field.widget.attrs["aria-required"] = "true" if field.required else "false"


class AuraAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Kullanıcı adı")
    password = forms.CharField(
        label="Şifre",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_common_field_attrs(
            self.fields["username"],
            "username",
            placeholder="Kullanıcı adınız",
            autocomplete="username",
        )
        apply_common_field_attrs(
            self.fields["password"],
            "password",
            placeholder="Şifreniz",
            autocomplete="current-password",
        )
        self.fields["username"].widget.attrs.setdefault("autofocus", "autofocus")


class AuraPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="E-posta adresi")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_common_field_attrs(
            self.fields["email"],
            "email",
            placeholder="ornek@universite.edu.tr",
            autocomplete="email",
        )
        self.fields["email"].widget.attrs.setdefault("autofocus", "autofocus")


class UserStatusActionForm(forms.Form):
    note = forms.CharField(
        label="İşlem notu",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Pasife alma veya yeniden aktive etme nedenini kısaca yazın.",
                "class": "input-field",
            }
        ),
    )

    def __init__(self, *args, require_note=False, **kwargs):
        self.require_note = require_note
        super().__init__(*args, **kwargs)
        self.fields["note"].help_text = (
            "Pasife alma işlemlerinde neden yazılması önerilir; bu not işlem geçmişinde görünür."
        )
        apply_common_field_attrs(self.fields["note"], "status_action_note")

    def clean_note(self):
        note = self.cleaned_data["note"].strip()
        if self.require_note and not note:
            raise forms.ValidationError("Kullanıcıyı pasife alırken kısa bir neden yazın.")
        return note

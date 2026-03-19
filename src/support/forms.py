import json

from django import forms
from django.utils import timezone

from users.models import User

from .models import (
    RequestMaterial,
    RequestMessage,
    SupportRequest,
    SupportRequestInterventionNote,
)


def apply_common_field_attrs(field, name, *, placeholder=None):
    field.widget.attrs.setdefault("class", "input-field")
    field.widget.attrs.setdefault("aria-required", "true" if field.required else "false")
    if placeholder:
        field.widget.attrs.setdefault("placeholder", placeholder)
    if field.help_text:
        field.widget.attrs.setdefault("aria-describedby", f"id_{name}_help")
    if isinstance(field.widget, forms.Textarea):
        field.widget.attrs.setdefault("spellcheck", "true")


class StudentSupportRequestForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = (
            "title",
            "category",
            "course_name",
            "topic",
            "description",
            "urgency",
            "duration_value",
            "duration_unit",
            "requested_completion_date",
            "preferred_timing",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "requested_completion_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "title": "Talep başlığı",
            "category": "Destek kategorisi",
            "course_name": "Ders adı",
            "topic": "Konu",
            "description": "İhtiyaç açıklaması",
            "urgency": "Aciliyet",
            "duration_value": "Süre",
            "duration_unit": "Süre birimi",
            "requested_completion_date": "Özel son tarih",
            "preferred_timing": "Uygun olduğunuz zamanlar",
        }
        placeholders = {
            "title": "Örneğin: İstatistik finali için tekrar desteği",
            "course_name": "Ders adını yazın",
            "topic": "Destek istediğiniz konuyu yazın",
            "description": "Ne tür bir desteğe ihtiyaç duyduğunuzu açık ve kısa biçimde yazın.",
            "duration_value": "Örneğin: 3",
            "preferred_timing": "Örneğin: Hafta içi 18.00 sonrası mesajlaşabilirim",
        }
        help_texts = {
            "category": "Talebinize en uygun kategoriyi seçin.",
            "description": "Akademik destek bağlamını, hedefinizi ve varsa materyal ihtiyacınızı belirtin.",
            "duration_value": "Bu desteğe ne kadar süre içinde (gün/hafta/ay) ihtiyacınız olduğunu sayı olarak yazın. Örneğin 3.",
            "duration_unit": "Gün, hafta veya ay seçebilirsiniz.",
            "requested_completion_date": "İsterseniz desteğin tamamlanması gereken özel bir tarih belirleyin.",
            "preferred_timing": "İletişim veya birlikte çalışma için uygun olduğunuz zaman aralığını yazabilirsiniz.",
        }
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            if name in help_texts:
                field.help_text = help_texts[name]
            apply_common_field_attrs(field, name, placeholder=placeholders.get(name))
        self.fields["duration_value"].widget.attrs.setdefault("min", "1")
        self.fields["title"].widget.attrs.setdefault("autofocus", "autofocus")
        self.fields["category"].widget.attrs["data-category-descriptions"] = json.dumps(
            SupportRequest.get_category_descriptions(),
            ensure_ascii=False,
        )
        self.fields["category"].widget.attrs["data-category-detail-target"] = "id_category_detail"

    def clean(self):
        cleaned_data = super().clean()
        duration_value = cleaned_data.get("duration_value")
        duration_unit = cleaned_data.get("duration_unit")
        requested_completion_date = cleaned_data.get("requested_completion_date")

        if duration_value and not duration_unit:
            self.add_error("duration_unit", "Süre girdiğinizde süre birimini de seçin.")
        if duration_unit and not duration_value:
            self.add_error("duration_value", "Süre birimi seçtiğinizde gün/hafta/ay sayısını da girin.")
        if requested_completion_date and requested_completion_date < timezone.localdate():
            self.add_error(
                "requested_completion_date",
                "Son tarih bugünden daha eski bir gün olamaz.",
            )

        return cleaned_data


class CoordinatorAssignmentForm(forms.Form):
    volunteer = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Gönüllü öğrenci",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["volunteer"].queryset = User.objects.filter(
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        ).order_by("first_name", "last_name", "username")
        self.fields["volunteer"].help_text = "Sadece profili tamamlanmış gönüllüler listelenir."
        apply_common_field_attrs(self.fields["volunteer"], "volunteer")


class CoordinatorRequestPriorityForm(forms.Form):
    priority = forms.ChoiceField(
        choices=SupportRequest.Priorities.choices,
        label="Talep önceliği",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["priority"].help_text = (
            "Bu alan koordinasyon sıralaması içindir; öğrenci tarafından görülen aciliyet alanından ayrıdır."
        )
        apply_common_field_attrs(self.fields["priority"], "priority")


class InterventionNoteForm(forms.ModelForm):
    class Meta:
        model = SupportRequestInterventionNote
        fields = ("priority", "body")
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Koordinasyon ekibi için kısa müdahale notu yazın.",
                    "class": "input-field",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["priority"].label = "Not önemi"
        self.fields["priority"].help_text = (
            "Önem sırası, koordinasyon notlarının özet panelinde hangi sırayla görüneceğini belirler."
        )
        self.fields["body"].label = "Koordinasyon notu"
        self.fields["body"].help_text = (
            "Bu not yalnızca koordinatör ve akademik danışman görünümünde yer alır."
        )
        apply_common_field_attrs(self.fields["priority"], "intervention_note_priority")
        apply_common_field_attrs(self.fields["body"], "intervention_note")


class RequestMessageForm(forms.ModelForm):
    class Meta:
        model = RequestMessage
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Mesajınızı buraya yazın.",
                    "class": "input-field",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["body"].label = "Mesaj"
        self.fields["body"].help_text = "Kısa, açık ve görev odaklı mesajlar iletişimi hızlandırır."
        apply_common_field_attrs(self.fields["body"], "body")


class RequestMaterialForm(forms.ModelForm):
    class Meta:
        model = RequestMaterial
        fields = ("title", "description", "file")
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Dosyanın ne olduğunu ve nasıl kullanılacağını kısaca açıklayın.",
                    "class": "input-field",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].label = "Materyal başlığı"
        self.fields["description"].label = "Materyal açıklaması"
        self.fields["file"].label = "Dosya"
        self.fields["description"].help_text = (
            "Materyalin içeriğini ve hangi amaçla kullanılacağını kısaca açıklayın."
        )
        self.fields["file"].help_text = "Yüklenen dosya talep içindeki ilgili kişilerle paylaşılır."
        apply_common_field_attrs(
            self.fields["title"],
            "title",
            placeholder="Örneğin: Makale özet notları",
        )
        apply_common_field_attrs(self.fields["description"], "description")
        apply_common_field_attrs(self.fields["file"], "file")
        self.fields["file"].widget.attrs.setdefault(
            "accept",
            ".pdf,.doc,.docx,.txt,.rtf,.png,.jpg,.jpeg",
        )


class StudentRequestMaterialForm(RequestMaterialForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].label = "Dosya başlığı"
        self.fields["description"].label = "Dosya hakkında kısa not"
        self.fields["file"].label = "Kaynak dosya"
        self.fields["description"].help_text = (
            "Bu dosyanın ne olduğunu ve gönüllüden nasıl bir destek beklediğinizi kısaca yazın."
        )
        self.fields["file"].help_text = (
            "PDF, ders notu, slayt, fotoğraf veya benzeri kaynağı ekleyebilirsiniz."
        )
        self.fields["title"].widget.attrs["placeholder"] = "Örneğin: İstatistik ders notları"
        self.fields["description"].widget.attrs["placeholder"] = (
            "Örneğin: Bu PDF'in erişilebilir özetini ve önemli formüllerin açıklanmasını istiyorum."
        )


class VolunteerRequestMaterialForm(RequestMaterialForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].help_text = (
            "Hazırladığınız özeti, açıklamayı veya destek çıktısını kısaca anlatın."
        )
        self.fields["file"].help_text = (
            "Yüklenen dosya öğrenci ve koordinasyon ekibiyle paylaşılır."
        )

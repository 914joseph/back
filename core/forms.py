from django import forms
from .models import AvaliacaoDesempenho, Colaborador, ItemAvaliacaoDesempenho, TipoItemAvaliacaoDesempenho


class AvaliacaoDesempenhoForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoDesempenho
        fields = '__all__'
        widgets = {
            'observacoes_avaliado': forms.Textarea(attrs={'rows': 3}),
            'sugestoes_supervisor': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk: 
            self.fields['status_avaliacao'].initial = AvaliacaoDesempenho.StatusAvaliacao.CRIADA
            self.fields['mes_competencia'].initial = AvaliacaoDesempenho.Meses.JANEIRO

    def clean(self):
        cleaned_data = super().clean()
        colaborador = cleaned_data.get("colaborador")
        supervisor = cleaned_data.get("supervisor")

        if colaborador == supervisor:
            raise forms.ValidationError(
                "O supervisor não pode ser o próprio colaborador.")
        if colaborador and colaborador.tipo != 1:
            raise forms.ValidationError(
                "O colaborador deve ser do tipo Colaborador.")
        if supervisor and supervisor.tipo != 2:
            raise forms.ValidationError(
                "O supervisor deve ser do tipo Supervisor.")


class ColaboradorForm(forms.ModelForm):
    class Meta:
        model = Colaborador
        fields = '__all__'

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        if not cpf.isdigit():
            raise forms.ValidationError(
                "CPF deve conter apenas dígitos numéricos.")
        if len(cpf) != 11:
            raise forms.ValidationError("CPF deve ter 11 dígitos.")
        if cpf == cpf[0] * 11:
            raise forms.ValidationError("CPF inválido.")
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = (sum1 * 10 % 11) % 10
        if digit1 != int(cpf[9]):
            raise forms.ValidationError("CPF inválido.")
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = (sum2 * 10 % 11) % 10
        if digit2 != int(cpf[10]):
            raise forms.ValidationError("CPF inválido.")
        return cpf


class ItemAvaliacaoDesempenhoForm(forms.ModelForm):
    class Meta:
        model = ItemAvaliacaoDesempenho
        fields = '__all__'
        widgets = {
            'nota': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }


class TipoItemAvaliacaoDesempenhoForm(forms.ModelForm):
    class Meta:
        model = TipoItemAvaliacaoDesempenho
        fields = '__all__'

from rest_framework import serializers
from .models import Colaborador, AvaliacaoDesempenho, ItemAvaliacaoDesempenho, TipoItemAvaliacaoDesempenho


class CollaboratorField(serializers.Field):
    def __init__(self, tipo=None, **kwargs):
        self.tipo = tipo
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, int):
            try:
                obj = Colaborador.objects.get(pk=data)
                if obj.tipo != self.tipo:
                    raise serializers.ValidationError(
                        f"Colaborador deve ter tipo {self.tipo}.")
                return obj
            except Colaborador.DoesNotExist:
                raise serializers.ValidationError(
                    "Colaborador não encontrado.")
        elif isinstance(data, dict):
            data = data.copy()
            data['tipo'] = self.tipo
            serializer = ColaboradorSerializer(data=data)
            if serializer.is_valid():
                return serializer.save()
            else:
                raise serializers.ValidationError(serializer.errors)
        else:
            raise serializers.ValidationError(
                "Deve ser um ID ou dicionário com nome e cpf.")

    def to_representation(self, value):
        return value.pk if value else None


class ColaboradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colaborador
        fields = '__all__'

    def validate_cpf(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "CPF deve conter apenas dígitos numéricos.")
        if len(value) != 11:
            raise serializers.ValidationError("CPF deve ter 11 dígitos.")
        if value == value[0] * 11:
            raise serializers.ValidationError("CPF inválido.")
        sum1 = sum(int(value[i]) * (10 - i) for i in range(9))
        digit1 = (sum1 * 10 % 11) % 10
        if digit1 != int(value[9]):
            raise serializers.ValidationError("CPF inválido.")
        sum2 = sum(int(value[i]) * (11 - i) for i in range(10))
        digit2 = (sum2 * 10 % 11) % 10
        if digit2 != int(value[10]):
            raise serializers.ValidationError("CPF inválido.")
        colaboradores_cpfs = Colaborador.objects.values_list('cpf', flat=True)
        if value in colaboradores_cpfs:
            raise serializers.ValidationError(
                "CPF já está cadastrado no sistema.")
        return value


class TipoItemAvaliacaoDesempenhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoItemAvaliacaoDesempenho
        fields = '__all__'


class ItemAvaliacaoDesempenhoSerializer(serializers.ModelSerializer):
    tipo_item_avaliacao_desempenho = serializers.PrimaryKeyRelatedField(
        queryset=TipoItemAvaliacaoDesempenho.objects.all())

    class Meta:
        model = ItemAvaliacaoDesempenho
        fields = '__all__'


class AvaliacaoDesempenhoSerializer(serializers.ModelSerializer):
    colaborador = CollaboratorField(tipo=1)
    supervisor = CollaboratorField(tipo=2)
    item_avaliacao_desempenho = ItemAvaliacaoDesempenhoSerializer(
        many=True, read_only=True)

    class Meta:
        model = AvaliacaoDesempenho
        fields = '__all__'
        read_only_fields = ['nota']

    def validate(self, data):
        colaborador = data.get('colaborador')
        supervisor = data.get('supervisor')
        if colaborador and supervisor:
            if colaborador == supervisor:
                raise serializers.ValidationError(
                    "O supervisor não pode ser o próprio colaborador.")
        return data

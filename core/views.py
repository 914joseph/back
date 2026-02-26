from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AvaliacaoDesempenho, ItemAvaliacaoDesempenho, TipoItemAvaliacaoDesempenho, Colaborador
from .serializers import (
    AvaliacaoDesempenhoSerializer,
    ItemAvaliacaoDesempenhoSerializer,
    TipoItemAvaliacaoDesempenhoSerializer,
    ColaboradorSerializer
)


def home(request):
    return HttpResponse("Olá! Meu back-end Django está online.")


class ColaboradorViewSet(viewsets.ModelViewSet):
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer

    def get_queryset(self):
        # Usar GET em vez de query_params para compatibilidade com linting
        tipo = self.request.GET.get('tipo')
        if tipo:
            try:
                tipo = int(tipo)
                return self.queryset.filter(tipo=tipo)
            except ValueError:
                return self.queryset.none()
        return self.queryset


class AvaliacaoDesempenhoViewSet(viewsets.ModelViewSet):
    queryset = AvaliacaoDesempenho.objects.all()
    serializer_class = AvaliacaoDesempenhoSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        avaliacao = self.get_object()
        try:
            avaliacao.iniciar()
            serializer = self.get_serializer(avaliacao)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='dar-feedback')
    def dar_feedback(self, request, pk=None):
        avaliacao = self.get_object()
        feedback = request.data.get('feedback', '')
        if not feedback:
            return Response({'error': 'Feedback é obrigatório'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            avaliacao.dar_feedback(feedback)
            serializer = self.get_serializer(avaliacao)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def concluir(self, request, pk=None):
        avaliacao = self.get_object()
        try:
            avaliacao.concluir()
            serializer = self.get_serializer(avaliacao)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='atualizar-nota')
    def atualizar_nota(self, request, pk=None):
        avaliacao = self.get_object()
        try:
            nota = avaliacao.atualizar_nota()
            serializer = self.get_serializer(avaliacao)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.pode_editar_avaliacao():
            return Response(
                {'error': 'Avaliação não pode ser editada neste status'},
                status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class ItemAvaliacaoDesempenhoViewSet(viewsets.ModelViewSet):
    queryset = ItemAvaliacaoDesempenho.objects.all()
    serializer_class = ItemAvaliacaoDesempenhoSerializer

    def get_queryset(self):
        avaliacao_pk = self.kwargs.get('avaliacao_pk')
        if avaliacao_pk:
            return self.queryset.filter(avaliacao_desempenho__pk=avaliacao_pk)
        return self.queryset

    """def perform_create(self, serializer):
        avaliacao_pk = self.kwargs.get('avaliacao_pk')
        if avaliacao_pk:
            avaliacao = AvaliacaoDesempenho.objects.get(pk=avaliacao_pk)
            if not avaliacao.pode_editar_itens():
                raise serializers.ValidationError(
                    'Itens não podem ser criados neste status')
            serializer.save(avaliacao_desempenho=avaliacao)
        else:
            serializer.save()"""

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.avaliacao_desempenho.pode_editar_itens():
            return Response(
                {'error': 'Item não pode ser editado neste status'},
                status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.avaliacao_desempenho.pode_editar_itens():
            return Response(
                {'error': 'Item não pode ser deletado neste status'},
                status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class TipoItemAvaliacaoDesempenhoViewSet(viewsets.ModelViewSet):
    queryset = TipoItemAvaliacaoDesempenho.objects.all()
    serializer_class = TipoItemAvaliacaoDesempenhoSerializer

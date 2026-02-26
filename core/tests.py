from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Colaborador, AvaliacaoDesempenho, ItemAvaliacaoDesempenho, TipoItemAvaliacaoDesempenho
from .serializers import ColaboradorSerializer, AvaliacaoDesempenhoSerializer, ItemAvaliacaoDesempenhoSerializer, TipoItemAvaliacaoDesempenhoSerializer

class ModelTests(TestCase):
    def setUp(self):
        self.colaborador = Colaborador.objects.create(nome='ColaboradorTeste', cpf='12345678901', tipo=1)
        self.supervisor = Colaborador.objects.create(nome='SupervisorTeste', cpf='98765432100', tipo=2)
        self.tipo_item1 = TipoItemAvaliacaoDesempenho.objects.create(
            dimensao='Comportamento', tipo_item_avaliacao_desempenho='Pontualidade', descricao='Teste1'
        )
        self.tipo_item2 = TipoItemAvaliacaoDesempenho.objects.create(
            dimensao='Competência', tipo_item_avaliacao_desempenho='Técnica', descricao='Teste2'
        )

    def test_colaborador_str(self):
        self.assertEqual(str(self.colaborador), "nome: ColaboradorTeste\ncpf: 12345678901")

    def test_avaliacao_unique_together(self):
        AvaliacaoDesempenho.objects.create(
            colaborador=self.colaborador, supervisor=self.supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        with self.assertRaises(Exception):  # Deve falhar por unique_together
            AvaliacaoDesempenho.objects.create(
                colaborador=self.colaborador, supervisor=self.supervisor, mes_competencia=1, sugestoes_supervisor='Outro'
            )

    def test_avaliacao_transicoes_estado(self):
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=self.colaborador, supervisor=self.supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        # Teste iniciar
        self.assertEqual(avaliacao.status_avaliacao, 'Criada')
        avaliacao.iniciar()
        self.assertEqual(avaliacao.status_avaliacao, 'Em elaboração')
        # Teste dar_feedback
        avaliacao.dar_feedback('Feedback')
        self.assertEqual(avaliacao.status_avaliacao, 'Em avaliação')
        # Teste concluir
        avaliacao.concluir()
        self.assertEqual(avaliacao.status_avaliacao, 'Concluída')
        # Teste erro em transição inválida
        with self.assertRaises(ValueError):
            avaliacao.iniciar()  # Já concluída

    def test_avaliacao_save_cria_itens(self):
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=self.colaborador, supervisor=self.supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        itens = ItemAvaliacaoDesempenho.objects.filter(avaliacao_desempenho=avaliacao)
        self.assertEqual(itens.count(), 2)  # Deve criar 1 item por tipo

    def test_atualizar_nota(self):
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=self.colaborador, supervisor=self.supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        avaliacao.status_avaliacao = 'Em elaboração'
        avaliacao.save()
        itens = ItemAvaliacaoDesempenho.objects.filter(avaliacao_desempenho=avaliacao)
        for item in itens:
            item.nota = 5
            item.save()
        avaliacao.atualizar_nota()
        self.assertEqual(avaliacao.nota, 100.0)  # (sum / (count*5)) * 100 = (10 / 10) * 100

    def test_pode_editar_itens(self):
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=self.colaborador, supervisor=self.supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        self.assertFalse(avaliacao.pode_editar_itens())  # Status CRIADA
        avaliacao.iniciar()
        self.assertTrue(avaliacao.pode_editar_itens())  # Status ELABORACAO
        avaliacao.dar_feedback('Feedback')
        self.assertFalse(avaliacao.pode_editar_itens())  # Status AVALIACAO

    def test_pode_editar_avaliacao(self):
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=self.colaborador, supervisor=self.supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        self.assertFalse(avaliacao.pode_editar_avaliacao())  # Status CRIADA
        avaliacao.iniciar()
        self.assertTrue(avaliacao.pode_editar_avaliacao())  # Status ELABORACAO
        avaliacao.dar_feedback('Feedback')
        self.assertTrue(avaliacao.pode_editar_avaliacao())  # Status AVALIACAO
        avaliacao.concluir()
        self.assertFalse(avaliacao.pode_editar_avaliacao())  # Status CONCLUIDA

class SerializerTests(TestCase):
    def test_colaborador_serializer_cpf_invalido(self):
        data = {'nome': 'ColaboradorTeste', 'cpf': '11111111111', 'tipo': 1}
        serializer = ColaboradorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cpf', serializer.errors)

    def test_colaborador_serializer_cpf_duplicado(self):
        Colaborador.objects.create(nome='ColaboradorTeste', cpf='67712006040', tipo=1)
        data = {'nome': 'Colaborador2Teste', 'cpf': '67712006040', 'tipo': 1}
        serializer = ColaboradorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cpf', serializer.errors)
        
    def test_avaliacao_serializer_tipos_invalidos(self):
        colaborador = Colaborador.objects.create(nome='ColaboradorTeste', cpf='12345678901', tipo=2)  # Tipo errado
        supervisor = Colaborador.objects.create(nome='SupervisorTeste', cpf='98765432100', tipo=1)  # Tipo errado
        data = {
            'colaborador': colaborador.id, 'supervisor': supervisor.id, 'mes_competencia': 1, 'sugestoes_supervisor': 'Teste'
        }
        serializer = AvaliacaoDesempenhoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('colaborador', serializer.errors)

    def test_item_avaliacao_serializer(self):
        colaborador = Colaborador.objects.create(nome='ColaboradorTeste', cpf='12345678901', tipo=1)
        supervisor = Colaborador.objects.create(nome='SupervisorTeste', cpf='98765432100', tipo=2)
        tipo = TipoItemAvaliacaoDesempenho.objects.create(
            dimensao='Comportamento', tipo_item_avaliacao_desempenho='Pontualidade', descricao='Teste Tipo'
        )
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=colaborador, supervisor=supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        data = {
            'observacoes': 'Teste obs',
            'nota': 3,
            'avaliacao_desempenho': avaliacao.id,
            'tipo_item_avaliacao_desempenho': tipo.id
        }
        serializer = ItemAvaliacaoDesempenhoSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_item_avaliacao_serializer_nota_invalida(self):
        colaborador = Colaborador.objects.create(nome='ColaboradorTeste', cpf='12345678901', tipo=1)
        supervisor = Colaborador.objects.create(nome='SupervisorTeste', cpf='98765432100', tipo=2)
        tipo = TipoItemAvaliacaoDesempenho.objects.create(
            dimensao='Comportamento', tipo_item_avaliacao_desempenho='Pontualidade', descricao='Teste Tipo'
        )
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=colaborador, supervisor=supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        data = {
            'observacoes': 'Teste obs',
            'nota': 6,  # Inválida
            'avaliacao_desempenho': avaliacao.id,
            'tipo_item_avaliacao_desempenho': tipo.id
        }
        serializer = ItemAvaliacaoDesempenhoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nota', serializer.errors)

    def test_tipo_item_serializer(self):
        data = {
            'dimensao': 'Comportamento',
            'tipo_item_avaliacao_desempenho': 'Pontualidade',
            'descricao': 'Teste Descricao'
        }
        serializer = TipoItemAvaliacaoDesempenhoSerializer(data=data)
        self.assertTrue(serializer.is_valid())

class APITests(APITestCase):
    def setUp(self):
        TipoItemAvaliacaoDesempenho.objects.create(
            dimensao='Comportamento', tipo_item_avaliacao_desempenho='Pontualidade', descricao='Competência Técnica'
        )
        self.colaborador = Colaborador.objects.create(nome='João', cpf='12345678901', tipo=1)
        self.supervisor = Colaborador.objects.create(nome='Maria', cpf='98765432100', tipo=2)
        self.avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=self.colaborador, supervisor=self.supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )

    def test_list_avaliacoes(self):
        url = reverse('avaliacaodesempenho-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_create_avaliacao(self):
        colaborador = Colaborador.objects.create(nome='Ana', cpf='11122233344', tipo=1)
        supervisor = Colaborador.objects.create(nome='Pedro', cpf='55566677788', tipo=2)
        url = reverse('avaliacaodesempenho-list')
        data = {
            'colaborador': colaborador.pk,
            'supervisor': supervisor.pk,
            'mes_competencia': 2, 'sugestoes_supervisor': 'Teste'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_iniciar_avaliacao(self):
        url = reverse('avaliacaodesempenho-iniciar', kwargs={'pk': self.avaliacao.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.avaliacao.refresh_from_db()
        self.assertEqual(self.avaliacao.status_avaliacao, 'Em elaboração')

    def test_editar_item_permitido(self):
        self.avaliacao.iniciar()  # Muda para ELABORACAO
        item = ItemAvaliacaoDesempenho.objects.filter(avaliacao_desempenho=self.avaliacao).first()
        self.assertIsNotNone(item)
        if item:
            url = reverse('avaliacao-item-detail', kwargs={'avaliacao_pk': self.avaliacao.pk, 'pk': item.pk})
            data = {'observacoes': 'Nova obs', 'nota': 4}
            response = self.client.patch(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_editar_item_bloqueado(self):
        self.avaliacao.status_avaliacao = 'Em avaliação'
        self.avaliacao.save()
        self.avaliacao.concluir()  # Muda para CONCLUIDA
        item = ItemAvaliacaoDesempenho.objects.filter(avaliacao_desempenho=self.avaliacao).first()
        self.assertIsNotNone(item)
        if item:
            url = reverse('avaliacao-item-detail', kwargs={'avaliacao_pk': self.avaliacao.pk, 'pk': item.pk})
            data = {'observacoes': 'Nova obs'}
            response = self.client.patch(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class APITestsDict(APITestCase):
    def setUp(self):
        TipoItemAvaliacaoDesempenho.objects.create(
            dimensao='Comportamento', tipo_item_avaliacao_desempenho='Pontualidade', descricao='Competência Técnica'
        )

    def test_create_avaliacao_with_dict(self):
        url = reverse('avaliacaodesempenho-list')
        data = {
            'colaborador': {'nome': 'Ana Dict', 'cpf': '12345678909'},
            'supervisor': {'nome': 'Pedro Dict', 'cpf': '98765432100'},
            'mes_competencia': 3, 'sugestoes_supervisor': 'Teste Dict'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_dar_feedback_avaliacao(self):
        colaborador = Colaborador.objects.create(nome='Ana', cpf='11122233344', tipo=1)
        supervisor = Colaborador.objects.create(nome='Pedro', cpf='55566677788', tipo=2)
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=colaborador, supervisor=supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        avaliacao.iniciar()  # Para ELABORACAO
        url = reverse('avaliacaodesempenho-dar-feedback', kwargs={'pk': avaliacao.pk})
        data = {'feedback': 'Novo feedback'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        avaliacao.refresh_from_db()
        self.assertEqual(avaliacao.status_avaliacao, 'Em avaliação')
        self.assertEqual(avaliacao.sugestoes_supervisor, 'Novo feedback')

    def test_concluir_avaliacao(self):
        colaborador = Colaborador.objects.create(nome='Ana', cpf='11122233344', tipo=1)
        supervisor = Colaborador.objects.create(nome='Pedro', cpf='55566677788', tipo=2)
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=colaborador, supervisor=supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        avaliacao.iniciar()
        avaliacao.dar_feedback('Feedback')  # Para AVALIACAO
        url = reverse('avaliacaodesempenho-concluir', kwargs={'pk': avaliacao.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        avaliacao.refresh_from_db()
        self.assertEqual(avaliacao.status_avaliacao, 'Concluída')

    def test_atualizar_nota_avaliacao(self):
        colaborador = Colaborador.objects.create(nome='Ana', cpf='11122233344', tipo=1)
        supervisor = Colaborador.objects.create(nome='Pedro', cpf='55566677788', tipo=2)
        avaliacao = AvaliacaoDesempenho.objects.create(
            colaborador=colaborador, supervisor=supervisor, mes_competencia=1, sugestoes_supervisor='Teste'
        )
        avaliacao.iniciar()
        itens = ItemAvaliacaoDesempenho.objects.filter(avaliacao_desempenho=avaliacao)
        for item in itens:
            item.nota = 4
            item.save()
        url = reverse('avaliacaodesempenho-atualizar-nota', kwargs={'pk': avaliacao.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        avaliacao.refresh_from_db()
        self.assertEqual(avaliacao.nota, 80.0)  # (sum / (count*5)) * 100 = (8 / 10) * 100 for 2 items
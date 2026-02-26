from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Count, Sum
import random


class Colaborador(models.Model):

    class Tipos(models.IntegerChoices):
        COLABORADOR = 1
        SUPERVISOR = 2
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=11)
    tipo = models.IntegerField(choices=Tipos.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"nome: {self.nome}\ncpf: {self.cpf}"


class AvaliacaoDesempenho(models.Model):

    class Meses(models.IntegerChoices):
        JANEIRO = 1, 'Janeiro'
        FEVEREIRO = 2, 'Fevereiro'
        MARCO = 3, 'Março'
        ABRIL = 4, 'Abril'
        MAIO = 5, 'Maio'
        JUNHO = 6, 'Junho'
        JULHO = 7, 'Julho'
        AGOSTO = 8, 'Agosto'
        SETEMBRO = 9, 'setembro'
        OUTUBRO = 10, 'Outubro'
        NOVEMBRO = 11, 'Novembro'
        DEZEMBRO = 12, 'Dezembro'

    class StatusAvaliacao(models.TextChoices):
        CRIADA = 'Criada'
        ELABORACAO = 'Em elaboração'
        AVALIACAO = 'Em avaliação'
        CONCLUIDA = 'Concluída'

    id = models.AutoField(primary_key=True)
    colaborador = models.ForeignKey(
        Colaborador,
        on_delete=models.CASCADE,
        related_name='colaborador')
    supervisor = models.ForeignKey(
        Colaborador,
        on_delete=models.CASCADE,
        related_name='supervisor')
    mes_competencia = models.PositiveSmallIntegerField(
        choices=Meses.choices)  # default=datetime.date.today().month
    status_avaliacao = models.CharField(
        max_length=20,
        choices=StatusAvaliacao.choices,
        default=StatusAvaliacao.CRIADA)
    nota = models.FloatField(default=0, blank=True)
    sugestoes_supervisor = models.TextField()
    observacoes_avaliado = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('colaborador', 'mes_competencia')

    def __str__(self):
        return f"Avaliação de {
            self.colaborador.nome} - Mês {
            self.mes_competencia}"

    def iniciar(self):
        """Transição: Criada -> Em elaboração. Só permite se status for CRIADA."""
        if self.status_avaliacao != self.StatusAvaliacao.CRIADA:
            raise ValueError(
                "A avaliação só pode ser iniciada se estiver no status 'Criada'.")
        self.status_avaliacao = self.StatusAvaliacao.ELABORACAO
        self.save()

    def dar_feedback(self, feedback: str) -> str:
        """Transição: Em elaboração -> Em avaliação. Só permite se status for ELABORACAO."""
        if self.status_avaliacao != self.StatusAvaliacao.ELABORACAO:
            raise ValueError(
                "Feedback só pode ser dado se a avaliação estiver 'Em elaboração'.")
        self.sugestoes_supervisor = feedback
        self.status_avaliacao = self.StatusAvaliacao.AVALIACAO
        self.save()
        return self.sugestoes_supervisor

    def concluir(self):
        """Transição: Em avaliação -> Concluída. Só permite se status for AVALIACAO."""
        if self.status_avaliacao != self.StatusAvaliacao.AVALIACAO:
            raise ValueError(
                "A avaliação só pode ser concluída se estiver 'Em avaliação'.")
        self.status_avaliacao = self.StatusAvaliacao.CONCLUIDA
        self.save()

    def atualizar_nota(self) -> float:
        """Atualiza a nota. Pode ser chamado em ELABORACAO, mas não muda status automaticamente."""
        if self.status_avaliacao not in [
                self.StatusAvaliacao.ELABORACAO,
                self.StatusAvaliacao.AVALIACAO]:
            raise ValueError(
                "Nota só pode ser atualizada se a avaliação estiver 'Em elaboração' ou 'Em avaliação'.")
        total_nota = ItemAvaliacaoDesempenho.objects.filter(
            avaliacao_desempenho=self).aggregate(
            Sum('nota'))['nota__sum'] or 0
        total_items = ItemAvaliacaoDesempenho.objects.filter(
            avaliacao_desempenho=self).count()

        if total_items > 0:
            self.nota = (total_nota / (total_items * 5)) * 100

        self.save()

        return self.nota

    def pode_editar_itens(self) -> bool:
        """Verifica se itens podem ser editados (só em ELABORACAO)."""
        return self.status_avaliacao == self.StatusAvaliacao.ELABORACAO

    def pode_editar_avaliacao(self) -> bool:
        """Verifica se avaliação pode ser editada (em ELABORACAO ou AVALIACAO)."""
        return self.status_avaliacao in [
            self.StatusAvaliacao.ELABORACAO,
            self.StatusAvaliacao.AVALIACAO]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            tipos = TipoItemAvaliacaoDesempenho.objects.all()
            for tipo in tipos:
                ItemAvaliacaoDesempenho.objects.create(
                    observacoes='',
                    nota=1,
                    avaliacao_desempenho=self,
                    tipo_item_avaliacao_desempenho=tipo
                )


class ItemAvaliacaoDesempenho(models.Model):

    id = models.AutoField(primary_key=True)
    observacoes = models.TextField()
    nota = models.SmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)])
    avaliacao_desempenho = models.ForeignKey(
        AvaliacaoDesempenho,
        on_delete=models.CASCADE,
        related_name='item_avaliacao_desempenho')
    tipo_item_avaliacao_desempenho = models.ForeignKey(
        'TipoItemAvaliacaoDesempenho', on_delete=models.CASCADE)

    def __str__(self):
        return f"Item:{
            self.observacoes} - nota:{
            self.nota} - avaliacao:{
            self.avaliacao_desempenho.colaborador.nome} - tipo:{
                self.tipo_item_avaliacao_desempenho.descricao}"


class TipoItemAvaliacaoDesempenho(models.Model):

    id = models.AutoField(primary_key=True)

    class DimensaoItemAvaliacao(models.TextChoices):
        COMPORTAMENTO = 'Comportamento'
        ENTREGAS = 'Entregas'
        TRAB_EQUIPE = 'Trabalho em equipe'

    dimensao = models.CharField(
        max_length=20,
        choices=DimensaoItemAvaliacao.choices)
    tipo_item_avaliacao_desempenho = models.TextField()
    descricao = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TipoItem:{
            self.tipo_item_avaliacao_desempenho} - dimensão:{
            self.dimensao} - descrição:{
            self.descricao}"

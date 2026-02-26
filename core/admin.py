from django.contrib import admin
from .models import AvaliacaoDesempenho, Colaborador, ItemAvaliacaoDesempenho, TipoItemAvaliacaoDesempenho
from .forms import AvaliacaoDesempenhoForm, ColaboradorForm, ItemAvaliacaoDesempenhoForm, TipoItemAvaliacaoDesempenhoForm
from django.contrib import messages


class ItemAvaliacaoDesempenhoInline(admin.TabularInline):
    model = ItemAvaliacaoDesempenho
    form = ItemAvaliacaoDesempenhoForm
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.pode_editar_itens():
            return ['observacoes', 'nota', 'tipo_item_avaliacao_desempenho']
        return []


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    form = ColaboradorForm
    list_display = ('nome', 'cpf', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('nome', 'cpf')


def iniciar_avaliacao(modeladmin, request, queryset):
    for avaliacao in queryset:
        try:
            avaliacao.iniciar()
            messages.success(
                request, f"Avaliação de {avaliacao.colaborador.nome} iniciada com sucesso.")
        except ValueError as e:
            messages.error(
                request, f"Erro ao iniciar avaliação de {avaliacao.colaborador.nome}: {str(e)}")


iniciar_avaliacao.short_description = "Iniciar avaliações selecionadas"


def dar_feedback_avaliacao(modeladmin, request, queryset):
    feedback = "Feedback fornecido via admin."
    for avaliacao in queryset:
        try:
            avaliacao.dar_feedback(feedback)
            messages.success(
                request, f"Feedback dado para avaliação de {avaliacao.colaborador.nome}.")
        except ValueError as e:
            messages.error(
                request, f"Erro ao dar feedback para {avaliacao.colaborador.nome}: {str(e)}")


dar_feedback_avaliacao.short_description = "Dar feedback para avaliações selecionadas"


def concluir_avaliacao(modeladmin, request, queryset):
    for avaliacao in queryset:
        try:
            avaliacao.concluir()
            messages.success(
                request, f"Avaliação de {avaliacao.colaborador.nome} concluída.")
        except ValueError as e:
            messages.error(
                request, f"Erro ao concluir avaliação de {avaliacao.colaborador.nome}: {str(e)}")


concluir_avaliacao.short_description = "Concluir avaliações selecionadas"


@admin.register(AvaliacaoDesempenho)
class AvaliacaoDesempenhoAdmin(admin.ModelAdmin):
    form = AvaliacaoDesempenhoForm
    list_display = (
        'colaborador',
        'supervisor',
        'mes_competencia',
        'status_avaliacao',
        'nota')
    list_filter = ('status_avaliacao', 'mes_competencia')
    search_fields = ('colaborador__nome', 'supervisor__nome')
    inlines = [ItemAvaliacaoDesempenhoInline]
    actions = [iniciar_avaliacao, dar_feedback_avaliacao, concluir_avaliacao]

    def get_inline_instances(self, request, obj=None):
        return super().get_inline_instances(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.pode_editar_avaliacao():
            return [
                'colaborador',
                'supervisor',
                'mes_competencia',
                'status_avaliacao',
                'nota',
                'sugestoes_supervisor',
                'observacoes_avaliado']
        return []


@admin.register(ItemAvaliacaoDesempenho)
class ItemAvaliacaoDesempenhoAdmin(admin.ModelAdmin):
    form = ItemAvaliacaoDesempenhoForm
    list_display = (
        'avaliacao_desempenho',
        'tipo_item_avaliacao_desempenho',
        'nota',
        'observacoes')
    list_filter = ('tipo_item_avaliacao_desempenho__dimensao',)
    search_fields = ('avaliacao_desempenho__colaborador__nome', 'observacoes')


@admin.register(TipoItemAvaliacaoDesempenho)
class TipoItemAvaliacaoDesempenhoAdmin(admin.ModelAdmin):
    form = TipoItemAvaliacaoDesempenhoForm
    list_display = ('dimensao', 'tipo_item_avaliacao_desempenho', 'descricao')
    list_filter = ('dimensao',)
    search_fields = ('tipo_item_avaliacao_desempenho', 'descricao')

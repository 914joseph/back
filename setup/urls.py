from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from core.views import (
    home,
    ColaboradorViewSet,
    AvaliacaoDesempenhoViewSet,
    ItemAvaliacaoDesempenhoViewSet,
    TipoItemAvaliacaoDesempenhoViewSet
)

router = DefaultRouter()
router.register(r'colaboradores', ColaboradorViewSet)
router.register(r'avaliacao', AvaliacaoDesempenhoViewSet)
router.register(r'tipoitem', TipoItemAvaliacaoDesempenhoViewSet)

# Para itens aninhados
avaliacao_router = DefaultRouter()
avaliacao_router.register(r'item', ItemAvaliacaoDesempenhoViewSet, basename='avaliacao-item')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('api/', include(router.urls)),
    path('api/avaliacao/<int:avaliacao_pk>/', include(avaliacao_router.urls)),
    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

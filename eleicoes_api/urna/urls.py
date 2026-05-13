from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EleitorViewSet, EleicaoViewSet, CandidatoViewSet, AptidaoEleitorViewSet, RegistroVotacaoViewSet, VotoViewSet


router = DefaultRouter()

router.register(r'eleitores', EleitorViewSet, basename='eleitores')
router.register(r'eleicoes', EleicaoViewSet, basename='eleicoes')
router.register(r'candidatos', CandidatoViewSet, basename='candidatos')
router.register(r'aptidoes', AptidaoEleitorViewSet, basename='aptidoes')
router.register(r'registros-votacao', RegistroVotacaoViewSet, basename='registros-votacao')
router.register(r'votos', VotoViewSet, basename='votos')

urlpatterns = [
    path('', include(router.urls)),
]
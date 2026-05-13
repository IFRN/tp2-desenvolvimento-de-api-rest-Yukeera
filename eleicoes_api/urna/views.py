from django.shortcuts import render
from rest_framework import viewsets 
from rest_framework.response import Response 
from rest_framework import status 
from django_filters.rest_framework import DjangoFilterBackend 
from rest_framework.filters import SearchFilter, OrderingFilter 

# Create your views here.

from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, RegistroVoto, Voto
from .serializers import EleitorSerializer, EleicaoSerializer, CandidatoSerializer, AptidaoEleitorSerializer, RegistroVotacaoSerializer, VotoSerializer

class EleitorViewSet(viewsets.ModelViewSet):
    queryset = Eleitor.objects.all()
    serializer_class = EleitorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['nome', 'email', 'cpf']
    filterset_fields = ['ativo']

class EleicaoViewSet(viewsets.ModelViewSet):
    queryset = Eleicao.objects.all()
    serializer_class = EleicaoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['titulo']
    filterset_fields = [ 'status', 'tipo', 'criada_por']
    ordering_fields = ['data_inicio', 'titulo']
    ordering = ['data_inicio']

class CandidatoViewSet(viewsets.ModelViewSet):
    queryset = Candidato.objects.select_related('eleicao').all()
    serializer_class = CandidatoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['nome', 'nome_urna', 'partido_ou_chapa']
    filterset_fields = ['eleicao']

class AptidaoEleitorViewSet(viewsets.ModelViewSet):
    queryset = AptidaoEleitor.objects.select_related('eleitor', 'eleicao').all()
    serializer_class = AptidaoEleitorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['eleitor', 'eleicao']

class RegistroVotacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegistroVoto.objects.all()
    serializer_class = RegistroVotacaoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['eleicao']
    ordering_fields = ['data_voto']
    ordering = ['-data_voto']

class VotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Voto.objects.all()
    serializer_class = VotoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['eleicao']
    

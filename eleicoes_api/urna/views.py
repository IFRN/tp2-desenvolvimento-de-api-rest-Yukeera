import secrets
from django.db import transaction, IntegrityError
from rest_framework.decorators import action
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

    @action(detail=True, methods=['post'], url_path='votar')
    def votar(self, request, pk=None):
        eleicao = self.get_object()
        
        input_data = request.data.copy()
        input_data['eleicao_id'] = eleicao.id

        serializer = VotacaoInputSerializer(data=input_data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        eleitor = validated_data['eleitor_obj']
        candidato_id = validated_data['candidato_id']
        em_branco = validated_data.get('em_branco', False)
        
        try:
            with transaction.atomic():
                try:
                    registro = RegistroVoto.objects.create(
                        eleitor=eleitor,
                        eleicao=eleicao
                    )
                except IntegrityError:
                    return Response(
                        {"detail": "Eleitor já votou nesta eleição."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                token_original = secrets.token_urlsafe(32)

                candidato = None
                candidato_str = "Voto em branco"

                if not em_branco:
                    candidato = Candidato.objects.get(id=candidato_id)
                    candidato_str = f"{candidato.nome_urna} ({candidato.numero})"

                voto = Voto.objects.create(
                    eleicao=eleicao,
                    candidato=candidato,
                    em_branco=em_branco,
                    comprovante_hash=token_original
                )

                resposta = {
                    "mensagem": "Voto registrado com sucesso.",
                    "comprovante": {
                        "token": token_original,
                        "eleicao": eleicao.titulo,
                        "data_hora": registro.data_hora,
                        "candidato": candidato_str,
                        "qr_code_url": f"/api/comprovantes/qr/?token={token_original}"
                    }
                }

                return Response(resposta, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"detail": f"Ocorreu um erro ao registrar o voto: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

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
    

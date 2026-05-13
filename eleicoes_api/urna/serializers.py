from datetime import timezone
import re
from rest_framework import serializers
from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, RegistroVoto, Voto

class EleitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eleitor
        fields = '__all__'

        def validate_cpf(self, value):
            cpf_regex = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
            if not re.match(cpf_regex, value):
                raise serializers.ValidationError(
                    "CPF deve estar no formato XXX.XXX.XXX-XX"
                )
            return value
        
class EleicaoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    total_candidatos = serializers.SerializerMethodField()
    total_aptos = serializers.SerializerMethodField()

    class Meta:
        model = Eleicao
        fields = [
            'id', 'titulo', 'descricao', 'tipo', 'data_inicio', 
            'data_fim', 'status', 'status_display', 'permite_branco', 
            'criada_por', 'total_candidatos', 'total_aptos'
        ]

    def get_total_candidatos(self, obj):
        return obj.candidatos.count()

    def get_total_aptos(self, obj):
        return obj.aptos.count()
    
class CandidatoSerializer(serializers.ModelSerializer):
    eleicao_titulo = serializers.CharField(source='eleicao.titulo', read_only=True)
    
    class Meta:
        model = Candidato
        fields = ['id', 'eleicao', 'eleicao_titulo', 'numero', 'nome', 'nome_urna', 'partido_ou_chapa', 'proposta', 'foto_url']

        def validate_numero(self, value):
            if value <= 0:
                raise serializers.ValidationError("O número do candidato não pode ser 0 (zero), pois este é reservado para votos em branco.")
            
            return value

class AptidaoEleitorSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.CharField(source='eleitor.nome', read_only=True)
    eleicao_titulo = serializers.CharField(source='eleicao.titulo', read_only=True)

    class Meta:
        model = AptidaoEleitor
        fields = ['id', 'eleitor', 'eleitor_nome', 'eleicao', 'eleicao_titulo', 'data_inclusao']

class RegistroVotacaoSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.CharField(source='eleitor.nome', read_only=True)
    eleicao_titulo = serializers.CharField(source='eleicao.titulo', read_only=True)

    class Meta:
        model = RegistroVoto
        fields = ['id', 'eleitor', 'eleitor_nome', 'eleicao', 'eleicao_titulo', 'data_hora']
        read_only_fields = fields

class VotoSerializer(serializers.ModelSerializer):
    candidato_nome_urna = serializers.CharField(source='candidato.nome_urna', read_only=True, allow_null=True)
    em_branco_display = serializers.SerializerMethodField()

    class Meta:
        model = Voto
        fields = ['id', 'eleicao', 'candidato', 'candidato_nome_urna', 'em_branco', 'em_branco_display', 'data_hora']
        read_only_fields = fields

    def get_em_branco_display(self, obj):
        if obj.em_branco:
            return "BRANCO"
        return None
    
class VotacaoInputSerializer(serializers.Serializer):
    eleitor_id = serializers.IntegerField()
    eleicao_id = serializers.IntegerField()
    candidato_id = serializers.IntegerField(required=False, allow_null=True)
    em_branco = serializers.BooleanField(default=False)

    def validate(self, data):
        eleitor_id = data.get('eleitor_id')
        eleicao_id = data.get('eleicao_id')
        candidato_id = data.get('candidato_id')
        em_branco = data.get('em_branco')

        if not em_branco and not candidato_id:
            raise serializers.ValidationError("Você deve escolher um candidato ou votar em branco.")
        if em_branco and candidato_id:
            raise serializers.ValidationError("Não é permitido escolher um candidato ao votar em branco.")
        
        try:
            eleicao = Eleicao.objects.get(id=eleicao_id)
        except Eleicao.DoesNotExist:
            raise serializers.ValidationError("Eleição não encontrada.")
        
        if eleicao.status != 'aberta':
            raise serializers.ValidationError("A eleição não está aberta para votação.")
        
        agora = timezone.now()
        if agora < eleicao.data_inicio or agora > eleicao.data_fim:
            raise serializers.ValidationError("A eleição não está no período de votação.")
        
        try:
            eleitor = Eleitor.objects.get(id=eleitor_id)
        except Eleitor.DoesNotExist:
            raise serializers.ValidationError("Eleitor não encontrado.")
        
        if not eleicao.aptos.filter(id=eleitor_id).exists():
            raise serializers.ValidationError("Eleitor não apto para votar nesta eleição.")
        
        if candidato_id:
            try:
                candidato = Candidato.objects.get(id=candidato_id)
                if candidato.eleicao_id != eleicao_id:
                    raise serializers.ValidationError("O candidato escolhido não pertence a esta eleição.")
            except Candidato.DoesNotExist:
                raise serializers.ValidationError("Candidato não encontrado.")
            
        data['eleicao_obj'] = eleicao
        data['eleitor_obj'] = eleitor

        return data
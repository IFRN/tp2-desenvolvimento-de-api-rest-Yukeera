from django.db import models
from django.core.exceptions import ValidationError
# Create your models here.

class Eleitor(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=14, unique=True) # Formato: 000.000.000-00
    data_nascimento = models.DateField()
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
    
class Eleicao(models.Model):
    TIPO_CHOICES = [
        ('estudantil', 'Estudantil'),
        ('sindical', 'Sindical'),
        ('associacao', 'Associação'),
        ('condominio', 'Condomínio'),
        ('conselho', 'Conselho'),
        ('outra', 'Outra'),
    ]

    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('aberta', 'Aberta'),
        ('encerrada', 'Encerrada'),
        ('apurada', 'Apurada'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(choices=TIPO_CHOICES)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    status = models.CharField(choices=STATUS_CHOICES, default='rascunho')
    permite_branco = models.BooleanField(default=True)
    criada_por = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='eleicoes_criadas')

    def __str__(self):
        return self.titulo
    
    def clean(self):
        super().clean()
        
        if self.data_inicio and self.data_fim:
            if self.data_fim <= self.data_inicio:
                raise ValidationError({
                    'data_fim': "A data de fim deve ser posterior à data de início."
                })
        
        if self.pk: 

            status_atual_db = Eleicao.objects.get(pk=self.pk).status
            novo_status = self.status

        if status_atual_db != novo_status:
            fluxo = ['rascunho', 'aberta', 'encerrada', 'apurada']
            try:
                indice_atual = fluxo.index(status_atual_db)
                indice_novo = fluxo.index(novo_status)

                if indice_novo < indice_atual:
                    raise ValidationError({
                        'status': f"Não é permitido voltar o status de {status_atual_db} para {novo_status}."
                    })
                
            except ValueError:
                raise ValidationError({'status': "Status inválido fornecido."})
   
class Candidato(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='candidatos')
    numero = models.PositiveIntegerField()
    nome = models.CharField(max_length=150)
    nome_urna = models.CharField(max_length=150)
    partido_ou_chapa = models.CharField(max_length=100, blank=True)
    proposta = models.TextField(blank=True)
    foto_url = models.URLField(blank=True)

    def __str__(self):
        return self.nome
    
    class Meta:
        unique_together = ('eleicao', 'numero')

class AptidaoEleitor(models.Model):
    eleitor = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='aptidoes')
    eleicao = models.ForeignKey(Eleicao, on_delete=models.PROTECT, related_name='aptos')
    data_inclusao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('eleitor', 'eleicao')

class RegistroVoto(models.Model):
    eleitor = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='registros_votacao')
    eleicao = models.ForeignKey(Eleicao, on_delete=models.PROTECT, related_name='registros_votacao')
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('eleitor', 'eleicao')

class Voto(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.PROTECT, related_name='votos')
    candidato = models.ForeignKey(Candidato, on_delete=models.PROTECT, related_name='votos', null=True, blank=True)
    em_branco = models.BooleanField(default=False)
    data_hora = models.DateTimeField(auto_now_add=True)
    comprovante_hash = models.CharField(max_length=64, unique=True)

    def clean(self):
        super().clean()

        if self.em_branco and self.candidato is not None:
            raise ValidationError("Um voto em branco não pode ter um candidato associado.")
        
        if not self.em_branco and self.candidato is None:
            raise ValidationError("Um voto que não é em branco deve ter um candidato associado.")
        

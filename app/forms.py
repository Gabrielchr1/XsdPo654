from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FloatField, DateField, IntegerField, SelectField, RadioField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField # <-- NOVA IMPORTAÇÃO
from app.models import Concessionaria # <-- NOVA IMPORTAÇÃO


# --- NOVA FUNÇÃO PARA POPULAR O QUERYSELECTFIELD ---
def concessionaria_query():
    return Concessionaria.query.order_by(Concessionaria.name)



class ProposalItemForm(FlaskForm):
    description = StringField('Descrição do Item', validators=[DataRequired()])
    quantity = IntegerField('Quantidade', default=1, validators=[DataRequired(), NumberRange(min=1)])
    unit_price = FloatField('Preço Unitário (R$)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Adicionar Item')



class ProposalForm(FlaskForm):
    """Formulário principal para criar/editar uma Proposta, com campos automáticos removidos."""
    
    # --- Grupo 1: Dados Gerais ---
    title = StringField('Título da Proposta', validators=[DataRequired()])
    valid_until = DateField('Válida Até', format='%Y-%m-%d', validators=[Optional()])

    # --- Grupo 2: Taxas e Concessionária ---
    kwh_price = FloatField('Valor da Tarifa de Energia (R$/kWh)', validators=[Optional()])
    public_lighting_fee = FloatField('Taxa de Iluminação Pública (R$)', validators=[Optional()])
    concessionaria = QuerySelectField('Concessionária', query_factory=concessionaria_query, get_label='name', allow_blank=True, blank_text='-- Selecione --')

    # --- Grupo 3: Consumo e Rede ---
    consumption_input_type = RadioField('Entrada de Consumo', choices=[('kwh', 'Consumo (kWh/mês)'), ('brl', 'Fatura (R$/mês)')], default='kwh')
    avg_consumption_kwh = FloatField('Consumo Médio Mensal (kWh)', validators=[Optional()])
    avg_bill_brl = FloatField('Valor Médio da Fatura (R$)', validators=[Optional()])
    grid_type = SelectField('Tipo de Rede', choices=[('monofasica', 'Monofásica'), ('bifasica', 'Bifásica'), ('trifasica', 'Trifásica')], validators=[DataRequired()])
    
    # --- Grupo 4: Dados para Cálculo Automático ---
    solar_irradiance = FloatField('Irradiação Solar Média (Hsp)', render_kw={'readonly': True})
    system_power_kwp = FloatField('Potência do Sistema (kWp)', validators=[Optional()])
    total_investment = FloatField('Investimento Total (R$)')
    
    # --- Grupo 5: Informações Adicionais ---
    notes = TextAreaField('Observações')
    
    submit = SubmitField('Salvar e Continuar')






class LoginForm(FlaskForm):
    # Usaremos 'username' como o nome do campo, mas o usuário poderá digitar username ou email.
    username = StringField(
        'Usuário ou E-mail', 
        validators=[DataRequired(message="Este campo é obrigatório.")],
        render_kw={"placeholder": "seu-usuario"}
    )
    password = PasswordField(
        'Senha', 
        validators=[DataRequired(message="Este campo é obrigatório."), Length(min=4, message="A senha é muito curta.")],
        render_kw={"placeholder": "********"}
    )
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')




class ClientForm(FlaskForm):
    client_type = StringField('Tipo de Cliente') # Será controlado pelo JS
    name = StringField('Nome Completo / Razão Social', validators=[DataRequired()])
    fantasy_name = StringField('Nome Fantasia')
    cpf_cnpj = StringField('CPF / CNPJ', validators=[DataRequired()])
    state_registration = StringField('Inscrição Estadual')
    
    email = StringField('E-mail', validators=[Optional(), Email()])
    phone = StringField('Telefone / WhatsApp')
    
    cep = StringField('CEP')
    address = StringField('Logradouro')
    number = StringField('Número')
    complement = StringField('Complemento')
    neighborhood = StringField('Bairro')
    city = StringField('Cidade')
    state = StringField('UF')

    submit = SubmitField('Salvar Cliente')




# --- NOVO FORMULÁRIO PARA O MODAL ---
class ConcessionariaForm(FlaskForm):
    name = StringField('Nome da Concessionária', validators=[DataRequired()])
    fio_b_price = FloatField('Valor do Fio B (R$/kWh)', validators=[DataRequired()])
    submit = SubmitField('Salvar')
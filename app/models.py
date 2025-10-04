from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return User.query.get(int(id))




# --- NOVA CLASSE PARA O CATÁLOGO DE PRODUTOS ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), index=True) # Ex: Módulo, Inversor, Estrutura, Mão de Obra
    manufacturer = db.Column(db.String(100))
    power_wp = db.Column(db.Integer) # Potência em Watts, para módulos
    warranty_years = db.Column(db.Integer) # Garantia em anos

    def __repr__(self):
        return f'<Product {self.name}>'





class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))


    proposals = db.relationship('Proposal', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_type = db.Column(db.String(10), default='PF') # PF para Pessoa Física, PJ para Jurídica
    name = db.Column(db.String(120), index=True, nullable=False) # Será Nome Completo ou Razão Social
    fantasy_name = db.Column(db.String(120)) # Nome Fantasia para PJ
    cpf_cnpj = db.Column(db.String(20), unique=True, index=True)
    state_registration = db.Column(db.String(20)) # Inscrição Estadual para PJ
    
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(20))
    
    # Campos de Endereço
    cep = db.Column(db.String(10))
    address = db.Column(db.String(200))
    number = db.Column(db.String(20))
    complement = db.Column(db.String(100))
    neighborhood = db.Column(db.String(100)) # Bairro
    city = db.Column(db.String(100))
    state = db.Column(db.String(2)) # UF

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    proposals = db.relationship('Proposal', backref='client', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Client {self.name}>'
    




class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(20), default='Rascunho', index=True)
    creation_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    total_investment = db.Column(db.Float)
    estimated_savings_per_year = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    # --- NOVOS CAMPOS DE DIMENSIONAMENTO ---
    panel_power_wp = db.Column(db.Integer) # Potência de cada painel em Watts (Ex: 550)
    panel_quantity = db.Column(db.Integer) # Quantidade de painéis

    # --- NOVO CAMPO ---
    recommended_inverter_kw = db.Column(db.Float)

    # --- NOVOS CAMPOS DE TAXAS E TARIFAS ---
    kwh_price = db.Column(db.Float) # Valor do kWh em R$
    public_lighting_fee = db.Column(db.Float) # Taxa de Iluminação Pública em R$
    
    # Relacionamento com a concessionária escolhida
    concessionaria_id = db.Column(db.Integer, db.ForeignKey('concessionaria.id'))
    concessionaria = db.relationship('Concessionaria')

    # --- NOVOS CAMPOS PARA CÁLCULO ---
    consumption_input_type = db.Column(db.String(10), default='kwh') # 'kwh' ou 'brl'
    avg_consumption_kwh = db.Column(db.Float)
    avg_bill_brl = db.Column(db.Float)
    grid_type = db.Column(db.String(20)) # Monofásica, Bifásica, Trifásica
    solar_irradiance = db.Column(db.Float) # Hsp (kWh/m²/dia)

    # --- NOVOS CAMPOS ---
    system_power_kwp = db.Column(db.Float) # Potência em kWp
    monthly_production_kwh = db.Column(db.JSON) # Armazenará os 12 valores de produção
    payback_years = db.Column(db.Float) # Payback em anos

    # Relacionamento: Uma proposta pertence a UM cliente
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    
    # Relacionamento: Uma proposta foi criada por UM usuário
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relacionamento: Uma proposta tem VÁRIOS itens
    items = db.relationship('ProposalItem', backref='proposal', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Proposal {self.title}>'
    

    






# --- CLASSE ATUALIZADA PARA OS ITENS DA PROPOSTA ---
# --- CLASSE ATUALIZADA PARA OS ITENS DA PROPOSTA ---
class ProposalItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float) # O preço pode variar por proposta
    total_price = db.Column(db.Float)

    # Conecta o item da proposta a um produto do catálogo
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product')

    # Conecta o item da proposta à proposta principal
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'), nullable=False)
    


# --- NOVA TABELA PARA CONCESSIONÁRIAS ---
class Concessionaria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    fio_b_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Concessionaria {self.name}>'
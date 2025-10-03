from flask import render_template, flash, redirect, url_for, request, Blueprint, Response, jsonify
import requests
from app import db
from app.forms import LoginForm, ClientForm, ProposalForm, ProposalItemForm, ConcessionariaForm
from app.models import User, Client, Proposal, ProposalItem, Concessionaria
from flask_login import current_user, login_user, logout_user, login_required
from app.utils import generate_monthly_production_chart, generate_payback_chart
from urllib.parse import urlsplit  # <-- LINHA CORRIGIDA
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

from weasyprint import HTML

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('index.html', title='Início')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
             user = User.query.filter_by(email=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Usuário ou senha inválidos.', 'danger')
            return redirect(url_for('main.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        next_page = request.args.get('next')
        # V-- LINHA CORRIGIDA
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
        
    return render_template('login.html', title='Login', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# ... (resto do arquivo)

@bp.route('/admin/dashboard')
@login_required
def dashboard():
    # A linha abaixo foi alterada
    return render_template("admin/dashboard.html", title="Dashboard")



@bp.route('/admin/clients')
@login_required
def clients():
    all_clients = Client.query.order_by(Client.name.asc())
    return render_template('admin/clients.html', title="Clientes", clients=all_clients)






@bp.route('/admin/client/add', methods=['GET', 'POST'])
@login_required
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        # Lógica para salvar os dados dos novos campos
        new_client = Client(
            client_type=form.client_type.data, name=form.name.data,
            fantasy_name=form.fantasy_name.data, cpf_cnpj=form.cpf_cnpj.data,
            state_registration=form.state_registration.data, email=form.email.data,
            phone=form.phone.data, cep=form.cep.data, address=form.address.data,
            number=form.number.data, complement=form.complement.data,
            neighborhood=form.neighborhood.data, city=form.city.data,
            state=form.state.data, user_id=current_user.id
        )
        db.session.add(new_client)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('main.clients'))
    return render_template('admin/client_form.html', title="Adicionar Cliente", form=form)

@bp.route('/admin/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client) # Pré-popula o formulário com os dados do cliente
    if form.validate_on_submit():
        client.client_type = form.client_type.data
        client.name = form.name.data
        # ... (atualize todos os outros campos da mesma forma) ...
        client.state = form.state.data
        db.session.commit()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('main.clients'))
    return render_template('admin/client_form.html', title="Editar Cliente", form=form)

@bp.route('/admin/client/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash('Cliente excluído com sucesso!', 'danger')
    return redirect(url_for('main.clients'))






# Rota para adicionar uma proposta a um cliente específico (VERSÃO CORRIGIDA)
@bp.route('/admin/client/<int:client_id>/proposal/add', methods=['GET', 'POST'])
@login_required
def add_proposal(client_id):
    client = Client.query.get_or_404(client_id)
    form = ProposalForm()
    
    if form.validate_on_submit():
        # --- INÍCIO DOS CÁLCULOS AUTOMÁTICOS ---

        # 1. CALCULAR PRODUÇÃO MENSAL E ANUAL
        # Fator de Performance: considera perdas por temperatura, sujeira, eficiência do inversor, etc. (valor padrão de 80%)
        performance_ratio = 0.80
        # Fatores sazonais para o hemisfério sul (verão produz mais, inverno menos)
        seasonal_factors = [1.1, 1.1, 1.0, 1.0, 0.9, 0.85, 0.85, 0.9, 1.0, 1.1, 1.15, 1.15]
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        monthly_prod_list = []
        if form.system_power_kwp.data and form.solar_irradiance.data:
            daily_avg_production = form.system_power_kwp.data * form.solar_irradiance.data * performance_ratio
            for i in range(12):
                monthly_production = daily_avg_production * days_in_month[i] * seasonal_factors[i]
                monthly_prod_list.append(round(monthly_production, 2))

        # 2. CALCULAR ECONOMIA ANUAL ESTIMADA
        annual_savings = 0
        if form.kwh_price.data and form.kwh_price.data > 0:
            # Primeiro, garante que temos o consumo em kWh
            consumption_kwh = form.avg_consumption_kwh.data
            if form.consumption_input_type.data == 'brl' and form.avg_bill_brl.data:
                # Estima o consumo em kWh a partir da fatura
                bill_for_consumption = form.avg_bill_brl.data - (form.public_lighting_fee.data or 0)
                consumption_kwh = bill_for_consumption / form.kwh_price.data

            # Custo de Disponibilidade (taxa mínima) em kWh, conforme regras da ANEEL
            grid_cost_kwh = {'monofasica': 30, 'bifasica': 50, 'trifasica': 100}.get(form.grid_type.data, 50)
            
            total_annual_production = sum(monthly_prod_list)
            total_annual_consumption = consumption_kwh * 12

            # O valor que o cliente economiza é a energia que ele gerou, descontando a taxa mínima
            # e a taxa do Fio B sobre a energia injetada na rede
            energia_a_ser_compensada = max(0, total_annual_production - (grid_cost_kwh * 12))
            energia_injetada = max(0, total_annual_production - total_annual_consumption)
            
            # Custo do Fio B (simplificado)
            fio_b_price = form.concessionaria.data.fio_b_price if form.concessionaria.data else 0
            custo_fio_b_anual = energia_injetada * fio_b_price

            # Economia total = (Energia compensada * tarifa) - custo do Fio B
            annual_savings = (energia_a_ser_compensada * form.kwh_price.data) - custo_fio_b_anual
        
        # --- FIM DOS CÁLCULOS AUTOMÁTICOS ---

        new_proposal = Proposal(
            title=form.title.data,
            kwh_price=form.kwh_price.data,
            public_lighting_fee=form.public_lighting_fee.data,
            concessionaria_id=form.concessionaria.data.id if form.concessionaria.data else None,
            consumption_input_type=form.consumption_input_type.data,
            avg_consumption_kwh=form.avg_consumption_kwh.data,
            avg_bill_brl=form.avg_bill_brl.data,
            grid_type=form.grid_type.data,
            solar_irradiance=form.solar_irradiance.data,
            system_power_kwp=form.system_power_kwp.data,
            total_investment=form.total_investment.data,
            valid_until=form.valid_until.data,
            notes=form.notes.data,
            client=client,
            author=current_user,
            
            # Atribui os valores calculados
            monthly_production_kwh=monthly_prod_list,
            estimated_savings_per_year=round(annual_savings, 2) if annual_savings > 0 else 0
        )

        # Calcula o payback simples
        if new_proposal.total_investment and new_proposal.estimated_savings_per_year:
            if new_proposal.estimated_savings_per_year > 0:
                new_proposal.payback_years = new_proposal.total_investment / new_proposal.estimated_savings_per_year

        db.session.add(new_proposal)
        db.session.commit()
        flash('Proposta criada com sucesso!', 'success')
        return redirect(url_for('main.proposal_detail', proposal_id=new_proposal.id))
    
    concessionaria_form = ConcessionariaForm()
    return render_template('admin/proposal_form.html', title="Nova Proposta", form=form, client=client, concessionaria_form=concessionaria_form)




# --- ROTA NOVA PARA O MODAL ---
@bp.route('/admin/concessionarias/add', methods=['POST'])
@login_required
def add_concessionaria():
    form = ConcessionariaForm()
    if form.validate_on_submit():
        new_concessionaria = Concessionaria(
            name=form.name.data,
            fio_b_price=form.fio_b_price.data
        )
        db.session.add(new_concessionaria)
        db.session.commit()
        # Retorna os dados da nova concessionária para o JavaScript
        return jsonify({
            'success': True, 
            'id': new_concessionaria.id, 
            'name': new_concessionaria.name
        })
    # Se a validação falhar, retorna os erros
    return jsonify({'success': False, 'errors': form.errors})




# --- ATUALIZE ESTA ROTA ---
@bp.route('/admin/proposal/<int:proposal_id>')
@login_required
def proposal_detail(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    # Passamos o formulário de item para o template para ser usado no modal
    item_form = ProposalItemForm()
    return render_template('admin/proposal_detail.html', title=proposal.title, proposal=proposal, item_form=item_form)



# Rota MÁGICA que gera o PDF
@bp.route('/admin/proposal/<int:proposal_id>/generate-pdf')
@login_required
def generate_pdf(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    
    # Gera os gráficos
    monthly_chart_b64 = generate_monthly_production_chart(proposal.monthly_production_kwh)
    payback_chart_b64 = generate_payback_chart(proposal.total_investment, proposal.estimated_savings_per_year)
    
    # Renderiza o template HTML passando os dados e os gráficos
    html_renderizado = render_template(
        'pdf/proposal_template.html', 
        proposal=proposal,
        monthly_chart_b64=monthly_chart_b64,
        payback_chart_b64=payback_chart_b64
    )
    
    # Usa o WeasyPrint para converter o HTML em PDF
    pdf = HTML(string=html_renderizado).write_pdf()

    # Retorna o PDF para download
    return Response(pdf, mimetype='application/pdf', headers={
        'Content-Disposition': f'attachment;filename=proposta_{proposal.client.name.replace(" ", "_")}.pdf'
    })


# --- ADICIONE ESTA NOVA ROTA ---
@bp.route('/admin/proposal/<int:proposal_id>/add_item', methods=['POST'])
@login_required
def add_item(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    form = ProposalItemForm()
    if form.validate_on_submit():
        # Cria o novo item
        item = ProposalItem(
            description=form.description.data,
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            total_price=form.quantity.data * form.unit_price.data,
            proposal_id=proposal.id
        )
        db.session.add(item)
        
        # Recalcula o valor total da proposta
        proposal.total_investment = sum(p_item.total_price for p_item in proposal.items)
        db.session.commit()
        flash('Item adicionado com sucesso!', 'success')
    else:
        flash('Erro ao adicionar item. Verifique os dados.', 'danger')
    return redirect(url_for('main.proposal_detail', proposal_id=proposal.id))


# --- ADICIONE ESTA OUTRA ROTA ---
@bp.route('/admin/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item_to_delete = ProposalItem.query.get_or_404(item_id)
    proposal = item_to_delete.proposal
    
    # Deleta o item
    db.session.delete(item_to_delete)
    
    # Recalcula o valor total da proposta
    proposal.total_investment = sum(p_item.total_price for p_item in proposal.items)
    db.session.commit()
    flash('Item removido com sucesso!', 'success')
    return redirect(url_for('main.proposal_detail', proposal_id=proposal.id))




@bp.route('/admin/get_irradiance/<int:client_id>')
@login_required
def get_irradiance(client_id):
    client = Client.query.get_or_404(client_id)
    
    if not client.address or not client.city or not client.state:
        return jsonify({'success': False, 'error': 'Endereço do cliente está incompleto. Por favor, preencha CEP, Cidade e Estado.'})
    
    try:
        geolocator = Nominatim(user_agent="solucao_solar_app_v1")
        address_string = f"{client.address}, {client.city}, {client.state}, Brazil"
        
        # Dica de depuração: veja o que está sendo enviado para a API
        print(f"--- Geocodificando endereço: {address_string}")
        
        location = geolocator.geocode(address_string, timeout=10)
        
        if location is None:
            return jsonify({'success': False, 'error': 'Endereço não encontrado. Tente ser mais específico no cadastro do cliente.'})
        
        lat, lon = location.latitude, location.longitude
        print(f"--- Coordenadas encontradas: Lat={lat}, Lon={lon}")

    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro de geocodificação: {e}'})

    try:
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=365)
        start = start_date.strftime('%Y%m%d')
        end = end_date.strftime('%Y%m%d')

        api_url = (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters=ALLSKY_SFC_SW_DWN&community=RE&latitude={lat}&longitude={lon}"
            f"&format=JSON&start={start}&end={end}"
        )
        
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        irradiance_data = data['properties']['parameter']['ALLSKY_SFC_SW_DWN']
        
        # --- A CORREÇÃO ESTÁ AQUI ---
        # 1. Filtra valores inválidos (a API da NASA usa -999 para dados ausentes)
        valid_values = [v for v in irradiance_data.values() if v >= 0]

        if not valid_values:
            return jsonify({'success': False, 'error': 'A API da NASA não retornou dados válidos para esta localidade.'})

        # 2. Calcula a média apenas com os valores válidos
        avg_irradiance = sum(valid_values) / len(valid_values)
        # --- FIM DA CORREÇÃO ---
        
        return jsonify({'success': True, 'irradiance': round(avg_irradiance, 2)})

    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Erro ao conectar à API da NASA: {e}'})
    except Exception as e:
        print(f"Erro ao processar dados da irradiação: {e}") # Adicionado para depuração
        return jsonify({'success': False, 'error': f'Erro inesperado ao processar dados da irradicação.'})
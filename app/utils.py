# app/utils.py

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

def generate_monthly_production_chart(data):
    """Gera um gráfico de barras da produção mensal e retorna como imagem base64."""
    if not data or len(data) != 12:
        return None # Retorna nada se não houver dados para os 12 meses

    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 5))

    bars = ax.bar(meses, data, color='#28a745')

    ax.set_title('Produção Mensal Estimada (kWh)', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Produção (kWh)')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.6)
    ax.xaxis.grid(False)
    
    # Adiciona os valores no topo das barras
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 5, f'{int(yval)}', ha='center', va='bottom')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def generate_payback_chart(investment, annual_savings, years=30):
    """Gera um gráfico de linha do payback e retorna como imagem base64."""
    if not investment or not annual_savings or investment <= 0 or annual_savings <= 0:
        return None

    cumulative_savings = np.cumsum([annual_savings] * years)
    year_axis = np.arange(1, years + 1)
    
    payback_year = investment / annual_savings
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(year_axis, cumulative_savings, color='#28a745', marker='o', linestyle='-', label='Economia Acumulada')
    ax.axhline(y=investment, color='#dc3545', linestyle='--', label='Investimento Inicial')
    
    # Ponto de payback
    ax.axvline(x=payback_year, color='grey', linestyle=':', label=f'Payback em {payback_year:.1f} anos')
    
    ax.set_title('Análise de Retorno do Investimento (Payback)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Anos')
    ax.set_ylabel('Valor (R$)')
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Formata o eixo Y para R$
    from matplotlib.ticker import FuncFormatter
    formatter = FuncFormatter(lambda y, _: f'R$ {int(y):,}'.replace(',', '.'))
    ax.yaxis.set_major_formatter(formatter)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')
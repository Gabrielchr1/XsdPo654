from app import create_app, db
from app.models import User
import click # Flask usa a biblioteca Click para criar comandos

app = create_app()

# O código abaixo cria um novo comando para o terminal
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.argument("password")
def create_admin_command(username, email, password):
    """Cria um novo usuário administrador."""
    # Verifica se o usuário ou email já existem
    if User.query.filter_by(username=username).first() is not None:
        print(f"Erro: O usuário '{username}' já existe.")
        return
    if User.query.filter_by(email=email).first() is not None:
        print(f"Erro: O e-mail '{email}' já está em uso.")
        return

    # Cria a instância do usuário, define a senha e salva
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Usuário administrador '{username}' criado com sucesso!")



# --- NOVO COMANDO PARA INICIALIZAR O BANCO DE DADOS ---
@app.cli.command("init-db")
def init_db_command():
    """Verifica se há usuários e, se não houver, cria o admin inicial."""
    if User.query.first() is not None:
        print("O banco de dados já contém usuários. O comando init-db não será executado.")
        return

    print("Banco de dados vazio. Criando usuário 'Admin' inicial...")
    admin_user = User(username='Admin', email='admin@solucaosolar.com')
    admin_user.set_password('123456') # Lembre-se de trocar por uma senha forte no futuro
    db.session.add(admin_user)
    db.session.commit()
    print("Usuário 'Admin' inicial criado com sucesso!")




if __name__ == '__main__':
    app.run(debug=True)
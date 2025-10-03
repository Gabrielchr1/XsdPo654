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


if __name__ == '__main__':
    app.run(debug=True)
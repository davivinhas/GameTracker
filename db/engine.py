from sqlalchemy import create_engine
import os

engine = create_engine(
    # String de conexão (alterar pra correta)
    "sqlite:///meu_banco.db",  # SQLite local

    # Parâmetros de configuração:
    echo=True,  # Mostra SQL gerado no console
    pool_size=5,  # Número de conexões no pool
    max_overflow=10,  # Conexões extras permitidas
    pool_recycle=3600,  # Recicla conexões a cada 1 hora
)
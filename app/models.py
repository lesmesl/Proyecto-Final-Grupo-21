from sqlalchemy import Column, Integer, String, DateTime
import datetime
from app.db import Base

class RegistroCarga(Base):
    __tablename__ = "registro_cargas"
    id = Column(Integer, primary_key=True, index=True)
    estado = Column(String, index=True)
    fecha_de_publicacion = Column(DateTime)
    fecha_de_consumo = Column(DateTime)

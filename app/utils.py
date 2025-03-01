import datetime
def get_fecha_actual():
    zona_horaria_colombia = datetime.timezone(datetime.timedelta(hours=-5), name="America/Bogota")
    return datetime.datetime.now(zona_horaria_colombia).isoformat()
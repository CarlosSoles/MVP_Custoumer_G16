# CambialoPe MVP

Sistema web de trueques y subastas desarrollado en Python con Flask.

## Requisitos Previos

- Python 3.x
- pip

## Instalación

1.  Instalar las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

2.  Configurar la base de datos:
    ```bash
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```
    *(Nota: Si ya se ha inicializado, solo ejecutar `flask db upgrade`)*

## Ejecución

Para iniciar el servidor de desarrollo:

```bash
python run.py
```

La aplicación estará disponible en: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Características

- **Usuarios**: Registro, Inicio de Sesión, Perfil, Coins (100 iniciales).
- **Objetos**: Publicar (-20 coins), Listar, Retirar, Eliminar.
- **Trueques**: Proponer, Aceptar, Confirmar (ventana de 5 min), Recompensa (+35 coins).
- **Notificaciones**: Alertas de estado de trueques.

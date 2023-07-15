from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from cloudinary.models import CloudinaryField

# OPCIONES PARA LOS ATRIBUTOS

ESTADO_CREDENCIAL = (
    ("activa", "Activa"),
    ("inactiva", "Inactiva"),
)

TIPO_CREDENCIAL = (
    ("alumno", "Alumno"),
    ("maestro", "Maestro"),
    ("administrativo", "Administrativo"),
)

TIPO_SOLICITUD = (
    ('nueva', 'Nueva'),
    ('renovacion', 'Renovacion'),
)

ESTADO_PARA_SOLICITUD = (
    ('pendiente', 'Pendiente'),
    ('aceptada', 'Aceptada'),
    ('rechazada', 'Rechazada'),
)


# notas:
#   Existen tres posibles estados para el estado de la solicitud: (pendiente, aceptada o rechazada)


# CREACION DE MODELOS NECESARIOS PARA ALUMNOS
class Carrera(models.Model):
    nombre = models.CharField(max_length=60)

    def __str__(self):
        return self.nombre


class Grado(models.Model):
    nombre = models.CharField(max_length=30)

    def __str__(self):
        return self.nombre


# Creacion de usuario base personalizado
class BaseUsuario(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe de tener un correo electronico")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        credencial = CredencialDigital.objects.create(usuario=user)
        ficha_medica = FichaMedica.objects.create(usuario=user)
        contacto_emergencia = ContactoEmergencia.objects.create(usuario=user)
        credencial.save()
        ficha_medica.save()
        contacto_emergencia.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=60)
    apellidos = models.CharField(max_length=60)

    numero_telefono = models.CharField(max_length=15)
    direccion = models.CharField(max_length=400)
    fecha_nacimiento = models.DateField()

    imagen_pefil = CloudinaryField('Imagen de perfil')

    # Datos para el sistema
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    objects = BaseUsuario()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def generar_solicitud_credencial_digital(self):
        if (self.credencial_digital.numero_activaciones == 0):
            tipo_solicitud = 'nueva'
        else:
            tipo_solicitud = 'renovacion'
        solicitud = SolicitudCredencialDigital.objects.create(tipo=tipo_solicitud, estado='pendiente', usuario=self)
        solicitud.save()
        return solicitud

    def activar_credencial_digital(self, fecha_vencimiento):
        self.credencial_digital.activar(fecha_vencimiento)
        self.credencial_digital.save()
        return

    def renovar_credencial_digital(self, fecha_vencimiento):
        self.credencial_digital.renovar(fecha_vencimiento)
        self.credencial_digital.save()
        return

    def desactivar_credencial_digital(self):
        self.credencial_digital.desactivar()
        self.credencial_digital.save()
        return

    def aceptar_solicitud_credencial_digital(self, fecha_vencimiento, solicitud):
        solicitud.estado_solicitud = 'aceptada'
        solicitud.save()
        self.activar_credencial_digital(fecha_vencimiento=fecha_vencimiento)
        return solicitud

    def rechazar_solicitud_credencial_digital(self, solicitud):
        solicitud.estado_solicitud = 'rechazada'
        solicitud.save()
        return solicitud

    def listar_solicitudes_credencial_digital(self):
        if self.solicitudes_credencial_digital.all().count() == 0:
            return None
        else:
            return self.solicitudes_credencial_digital.all()

    def existen_detalles_credencial_fisica(self):
        if self.detalles_credencial_fisica.all().count() == 0:
            return False
        else:
            return True

    def generar_solicitud_credencial_fisica(self):
        if self.existen_detalles_credencial_fisica():
            tipo_solicitud = 'renovacion'
        else:
            tipo_solicitud = 'nueva'
        solicitud = SolicitudCredencialFisica.objects.create(estado_solicitud='pendiente', tipo_solicitud=tipo_solicitud, usuario=self)

    def generar_detalle_credencial_fisica(self, tipo_credencial):
        detalle = DetalleCredenciaFisica.objects.create(tipo_credencial=tipo_credencial, usuario=self)
        detalle.save()
        return detalle


    def aceptar_solicitud_credencial_fisica(self, solicitud):
        solicitud.estado_solicitud = 'aceptada'
        solicitud.save()
        self.generar_credencial_fisica()
        self.generar_detalle_credencial_fisica(tipo_credencial=solicitud.tipo_credencial)
        return solicitud

    def rechazar_solicitud_credencial_fisica(self, solicitud):
        solicitud.estado_solicitud = 'rechazada'
        solicitud.save()
        return solicitud

    def obtener_ultima_solitud_realizada_credencial_fisica(self):
        if self.solicitudes_credencial_fisica.all().count() == 0:
            return None
        else:
            return self.solicitudes_credencial_fisica.all().last()

    def obtener_ultima_solicitud_realizada_credencial_digital(self):
        if self.solicitudes_credencial_digital.all().count() == 0:
            return None
        else:
            return self.solicitudes_credencial_digital.all().last()

    def __str__(self):
        return f'{self.nombre} {self.apellidos}'



class Alumno(Usuario):
    matricula = models.CharField(max_length=20)
    grado = models.ForeignKey(Grado, on_delete=models.RESTRICT)
    carrera = models.ForeignKey(Carrera, on_delete=models.RESTRICT)

    def __str__(self):
        return f'{self.nombre} {self.apellidos}'


class Maestro(Usuario):
    titulo_academico = models.CharField(max_length=60)

    def __str__(self):
        return f'{self.nombre} {self.apellidos}'


class Administrativo(Usuario):
    departamento = models.CharField(max_length=60)

    def __str__(self):
        return f'{self.nombre} {self.apellidos}'


# CREACION DE MODELOS NECESARIOS QUE TENDRAN TODOS LOS USUARIOS
class CredencialDigital(models.Model):
    estado = models.CharField(max_length=20, choices=ESTADO_CREDENCIAL, default='inactiva')
    fecha_expedicion = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True)
    numero_activaciones = models.IntegerField(default=0)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='credencial_digital')

    def activar(self, fecha_vencimiento=None):
        self.estado = 'activa'
        self.numero_activaciones += 1
        if fecha_vencimiento:
            self.fecha_vencimiento = fecha_vencimiento
        return

    def desactivar(self):
        self.estado = 'inactiva'
        return

    def __str__(self):
        return self.estado


class ContactoEmergencia(models.Model):
    nombre_contacto = models.CharField(max_length=70, null=True)
    numero_telefono = models.CharField(max_length=15, null=True)
    llenado = models.BooleanField(default=False)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='contactos_emergenciales')

    def __str__(self):
        return self.nombre_contacto


class FichaMedica(models.Model):
    tipo_sangre = models.CharField(max_length=10, null=True)
    alergias = models.CharField(max_length=200, null=True)
    medicamentos = models.CharField(max_length=200, null=True)
    llenado = models.BooleanField(default=False)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='ficha_medica')

    def __str__(self):
        return self.tipo_sangre


class SolicitudCredencialDigital(models.Model):
    estado_solicitud = models.CharField(max_length=20, choices=ESTADO_PARA_SOLICITUD, default='pendiente')
    fecha_solicitud = models.DateField(auto_now_add=True)
    tipo_solicitud = models.CharField(max_length=20, choices=TIPO_SOLICITUD, default='nueva')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='solicitudes_credencial_digital')

    def __str__(self):
        return self.estado_solicitud


class SolicitudCredencialFisica(models.Model):
    estado_solicitud = models.CharField(max_length=20, choices=ESTADO_PARA_SOLICITUD, default='pendiente')
    fecha_solicitud = models.DateField(auto_now_add=True)
    tipo_solicitud = models.CharField(max_length=20, choices=TIPO_SOLICITUD, default='nueva')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='solicitudes_credencial_fisica')

    def __str__(self):
        return self.estado_solicitud


class DetalleCredenciaFisica(models.Model):
    fecha_expedicion = models.DateField(auto_now_add=True)
    entrega = models.BooleanField(default=False)
    tipo_credencial = models.CharField(max_length=20, choices=TIPO_CREDENCIAL, default='nueva')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='detalles_credencial_fisica')

    def __str__(self):
        return self.tipo_credencial



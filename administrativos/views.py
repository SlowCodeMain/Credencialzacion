from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpRequest
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate, login, logout
from core.models import *


def parser(user: str, email):
    model = None
    match user:
        case "administrativo":
            try:
                model: Administrativo = Administrativo.objects.get(email=email)
                return model
            except:
                return None
        case _:
            pass


class AdminLogin(View):

    def get(self, request: HttpRequest):
        if request.user.is_authenticated:
            return redirect("home")
        else:
            return render(request, "administrativos/login/view_login_administradores.html", )


    def post(self, request: HttpRequest):
        email = request.POST.get("email")
        password = request.POST.get("password")

        administrativo: Administrativo = parser("administrativo", email)

        if administrativo is not None:
            if administrativo.check_password(password):
                login(authenticate(request, email=email, password=password))
                return redirect("home")
            else:
                return render(request, "administrativos/login/view_login_administradores.html", context={"error": "Contraseña inválida"})
        else:
            return render(request, "administrativos/login/view_login_administradores.html", context={"error": "Administrativo inexistente"})


class AdminLogout(View):
    def get(self, request: HttpRequest):
        logout(request)
        return redirect("")


class AdminCreate(View):

    def get(self, request: HttpRequest):
        return render(request, 'administrativos/crear/view_crear_administradores.html')

    def post(self, request: HttpRequest):
        nombre = request.POST.get('nombres')
        apellidos = request.POST.get('apellidos')
        email = request.POST.get('email')
        numero_telefono = request.POST.get('numero_telefono')
        direccion = request.POST.get('direccion')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        departamento = request.POST.get('departamento')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        imagen = request.FILES.get('imagen')

        parser: Administrativo = Administrativo.objects.filter(email=email).exists()

        if parser is False:
            if password1 == password2:
                administrador = Administrativo.objects.create(
                    email=email,
                    nombre=nombre,
                    apellidos=apellidos,
                    numero_telefono=numero_telefono,
                    direccion=direccion,
                    fecha_nacimiento=fecha_nacimiento,
                    departamento=departamento,
                    password=password1,
                    tipo_usuario='administrativo',
                    imagen_perfil=imagen
                )
                administrador.is_superuser = True
                administrador.is_staff = True
                administrador.save()

                return render(request, "administrativos/crear/view_crear_administradores.html", context={'success': 'Administrador creado correctamente, iniciar sesion: '})

            else:
                return render(request, "", context={"error": "Las contraseñas no coinciden"})
        else:
            return render(request, "", context={"error": "Éste correo ya existe"})


class AdminDetail(View):

    def get(self, request: HttpRequest):

        if request.user.is_authenticated:
            administrativo: Administrativo = parser("administrativo", request.user.email)
            print(administrativo.tipo_usuario)


# si estas validando que solo administradores puedan entrar hay un campo en el usuaro que te dice que tipo de usuario es
# perdon padre se me olvido agregarlo
# dame un segundo hago las migraciones
#Ya no estaba ese atributo en los modelos
#Si está, ya lo ví
# al momento de crear el usuario tienes que indicarle que tipo de usuario es
#ok
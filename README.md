# UPClink VPN

Plasmoide para KDE Plasma 6 que permite gestionar la conexión VPN UPClink de la Universitat Politècnica de Catalunya mediante autenticación SSO.

> Proyecto independiente. No es una aplicación oficial de la UPC.

## Autoría

Desarrollado por **Pep Simo** con la colaboración de **Claude (Anthropic)**.

Web: [www.pepsimo.eu](https://www.pepsimo.eu)

## Funciones

- Conexión y desconexión desde el panel de Plasma.
- Autenticación SSO mediante el navegador.
- Estados reactivos mediante señales D-Bus.
- Contador del tiempo de conexión.
- Integración con PolicyKit para operaciones privilegiadas.
- Ejecución de `openfortivpn` mediante un servicio del sistema.
- No almacena usuarios, contraseñas, cookies ni tokens SAML.
- Compatible con KDE Plasma 6 y Wayland.

## Privacidad

- El backend nunca expone credenciales, cookies de sesión ni tokens SAML por D-Bus; los mensajes de estado y de error se sanean y se reducen a categorías genéricas antes de mostrarse.
- Al desplegar el panel, el plasmoide comprueba como máximo una vez cada 24 horas si hay una versión nueva publicada, mediante una petición HTTPS anónima a `api.github.com` (sin enviar ningún dato personal ni identificador). Esta comprobación no se realiza si el panel no se abre.
- Ningún dato de la conexión VPN (usuario, contraseña, cookies, tokens) sale del propio equipo salvo hacia el servidor VPN de la UPC.

## Arquitectura

```text
Plasmoide QML
    ↓
Plugin Qt 6/C++
    ↓
D-Bus del sistema
    ↓
Backend Python
    ↓
PolicyKit
    ↓
openfortivpn
```

## Requisitos

- KDE Plasma 6.
- Qt 6 y Kirigami 6.
- `openfortivpn` con soporte para SAML.
- Python 3 con D-Bus y PyGObject.
- PolicyKit y systemd.

## Compilación y creación del RPM

```bash
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
cmake --build build --target package --parallel
./packaging/rpm/sign-package.sh dist/upclink-vpn-1.0.2-1.x86_64.rpm
```

El paquete resultante se genera en `dist/`.

## Descarga

Abre la [última versión publicada en GitHub](https://github.com/pepsimo/upclink-vpn/releases/latest).

En el apartado **Assets**, descarga estos tres archivos:

1. `upclink-vpn-1.0.2-1.x86_64.rpm` — instalador de la aplicación.
2. `upclink-vpn-1.0.2-1.x86_64.rpm.sha256` — comprobación de integridad.
3. `RPM-GPG-KEY-Pep-Simo.asc` — clave pública para verificar la firma del RPM.

Los archivos **Source code (zip)** y **Source code (tar.gz)** los genera GitHub automáticamente y no son necesarios para instalar la aplicación.

## Instalación

Guarda los tres archivos en la misma carpeta. Si están en `Descargas`, abre una terminal y ejecuta:

```bash
cd ~/Descargas
```

Comprueba que el RPM descargado no esté dañado ni haya sido modificado:

```bash
sha256sum -c upclink-vpn-1.0.2-1.x86_64.rpm.sha256
```

El resultado debe indicar que **la suma coincide**.

Importa la clave pública de firma:

```bash
sudo rpm --import RPM-GPG-KEY-Pep-Simo.asc
```

Instala UPClink VPN y sus dependencias:

```bash
sudo zypper install ./upclink-vpn-1.0.2-1.x86_64.rpm
```

## Añadir UPClink VPN al panel

1. Haz clic con el botón derecho en una zona vacía del panel inferior de KDE.
2. Selecciona **Añadir elementos gráficos**.
3. Busca **UPClink VPN**.
4. Arrastra el widget hasta el panel o haz doble clic sobre él para añadirlo.

Plasma no añade automáticamente el widget para evitar modificar sin permiso la configuración personal del escritorio.

## Conectarse a UPClink

La conexión se realiza en dos pasos:

1. Pulsa el icono de **UPClink VPN** del panel y selecciona **Conectar**. Si KDE solicita autorización, introduce la contraseña de administrador en la ventana de PolicyKit.
2. Pulsa **Abrir autenticación SSO** y completa la identificación de la UPC en el navegador.

Cuando se establezca la conexión, el widget mostrará el estado **Conectado** y el tiempo de conexión.

Para finalizar la VPN, abre nuevamente el widget y pulsa **Desconectar**.

## Desinstalación

```bash
sudo zypper remove upclink-vpn
```

## Seguridad

Las operaciones privilegiadas se realizan en un servicio del sistema protegido mediante PolicyKit. El plasmoide no ejecuta comandos como administrador ni guarda credenciales, cookies o tokens de autenticación.

## Licencia

Este proyecto se distribuye bajo la licencia **GPL-3.0-or-later**. Consulta el archivo `LICENSE`.

## Verificación del RPM

Los paquetes RPM se firman con la clave pública de Pep Simo.

Huella digital:

`160E 9104 CCFF 6878 BD2F 8EEA FCF7 348E 7E13 A874`

Antes de importar la clave, compara siempre esta huella:

```bash
gpg --show-keys --fingerprint packaging/keys/RPM-GPG-KEY-Pep-Simo.asc
sudo rpm --import packaging/keys/RPM-GPG-KEY-Pep-Simo.asc
rpm -Kv dist/upclink-vpn-1.0.2-1.x86_64.rpm
sha256sum -c dist/upclink-vpn-1.0.2-1.x86_64.rpm.sha256
```

# UPClink VPN

Plasmoide para KDE Plasma 6 que permite gestionar la conexión VPN UPClink de la Universitat Politècnica de Catalunya mediante autenticación SSO.

> Proyecto independiente. No es una aplicación oficial de la UPC.

## Autoría

Desarrollado por **Pep Simo** con la colaboración de **ChatGPT 5.6 Sol (OpenAI)**.

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
./packaging/rpm/sign-package.sh dist/upclink-vpn-1.0.0-1.x86_64.rpm
```

El paquete resultante se genera en `dist/`.

## Instalación

```bash
sudo zypper install ./dist/upclink-vpn-1.0.0-1.x86_64.rpm
```

Después de instalarlo, añade **UPClink VPN** al panel de Plasma desde el selector de elementos gráficos.

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
rpm -Kv dist/upclink-vpn-1.0.0-1.x86_64.rpm
sha256sum -c dist/upclink-vpn-1.0.0-1.x86_64.rpm.sha256
```

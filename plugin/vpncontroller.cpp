#include "vpncontroller.h"

#include <QDBusConnection>
#include <QDBusReply>
#include <QVariantMap>

VpnController::VpnController(QObject *parent)
    : QObject(parent)
    , m_interface(
        "org.upclink.VPN",
        "/org/upclink/VPN",
        "org.upclink.VPN",
        QDBusConnection::systemBus())
{
    const bool signalConnected =
        QDBusConnection::systemBus().connect(
            QStringLiteral("org.upclink.VPN"),
            QStringLiteral("/org/upclink/VPN"),
            QStringLiteral("org.upclink.VPN"),
            QStringLiteral("StateChanged"),
            this,
            SLOT(handleStateChanged(QString,QString,qlonglong))
        );

    getStatus();

    if (!signalConnected) {
        updateStatus(
            QStringLiteral("error"),
            QStringLiteral("No se pudo recibir la señal de estado D-Bus."),
            0
        );
    }
}

QString VpnController::state() const
{
    return m_state;
}

QString VpnController::message() const
{
    return m_message;
}

qint64 VpnController::connectedSince() const
{
    return m_connectedSince;
}

void VpnController::updateStatus(
    const QString &state,
    const QString &message,
    qint64 connectedSince
)
{
    if (m_state != state) {
        m_state = state;
        emit stateChanged();
    }

    if (m_message != message) {
        m_message = message;
        emit messageChanged();
    }

    if (m_connectedSince != connectedSince) {
        m_connectedSince = connectedSince;
        emit connectedSinceChanged();
    }
}

void VpnController::handleStateChanged(
    const QString &state,
    const QString &message,
    qlonglong connectedSince
)
{
    updateStatus(state, message, connectedSince);
}

QString VpnController::getStatus()
{
    QDBusReply<QVariantMap> reply = m_interface.call("GetStatus");

    if (!reply.isValid()) {
        updateStatus(
            QStringLiteral("error"),
            reply.error().message(),
            0
        );

        return m_state;
    }

    const QVariantMap status = reply.value();

    updateStatus(
        status.value("state").toString(),
        status.value("message").toString(),
        status.value("connected_since").toLongLong()
    );

    return m_state;
}

bool VpnController::connectVpn()
{
    QDBusReply<QString> reply = m_interface.call("Connect");
    return reply.isValid();
}

bool VpnController::disconnectVpn()
{
    QDBusReply<QString> reply = m_interface.call("Disconnect");
    return reply.isValid();
}

QString VpnController::authenticationUrl()
{
    QDBusReply<QString> reply =
        m_interface.call("GetAuthenticationUrl");

    if (!reply.isValid()) {
        return QString();
    }

    return reply.value();
}

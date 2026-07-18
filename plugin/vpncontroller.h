#pragma once

#include <QObject>
#include <QDBusInterface>
#include <QString>
#include <QtGlobal>
#include <qqmlintegration.h>

class VpnController : public QObject
{
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(QString state READ state NOTIFY stateChanged)
    Q_PROPERTY(QString message READ message NOTIFY messageChanged)
    Q_PROPERTY(qint64 connectedSince READ connectedSince NOTIFY connectedSinceChanged)

public:
    explicit VpnController(QObject *parent = nullptr);

    QString state() const;
    QString message() const;
    qint64 connectedSince() const;

    Q_INVOKABLE QString getStatus();
    Q_INVOKABLE bool connectVpn();
    Q_INVOKABLE bool disconnectVpn();
    Q_INVOKABLE QString authenticationUrl();

signals:
    void stateChanged();
    void messageChanged();
    void connectedSinceChanged();

private slots:
    void handleStateChanged(
        const QString &state,
        const QString &message,
        qlonglong connectedSince
    );

private:
    void updateStatus(
        const QString &state,
        const QString &message,
        qint64 connectedSince
    );

    QDBusInterface m_interface;
    QString m_state = QStringLiteral("disconnected");
    QString m_message;
    qint64 m_connectedSince = 0;
};

import QtQuick
import QtQuick.Layouts
import QtCore

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support

PlasmoidItem {
    id: root

    property string vpnState: "disconnected"
    property string lastMessage: ""

    readonly property string helper:
        "$HOME/.local/bin/upclink-plasma-control"

    readonly property string stateText: {
        if (vpnState === "connected") {
            return "Conectada"
        }

        if (vpnState === "connecting") {
            return "Esperando autenticación SSO"
        }

        return "Desconectada"
    }

    readonly property color stateColor: {
        if (vpnState === "connected") {
            return "#27ae60"
        }

        if (vpnState === "connecting") {
            return "#f1c40f"
        }

        return "#7f8c8d"
    }

    toolTipMainText: "UPClink VPN"
    toolTipSubText: stateText

    Plasmoid.icon: "network-vpn"

    function refreshState() {
        const command = helper + " status"

        if (statusSource.connectedSources.indexOf(command) === -1) {
            statusSource.connectSource(command)
        }
    }

    function runAction(actionName) {
        const command = helper + " " + actionName

        if (actionSource.connectedSources.indexOf(command) === -1) {
            actionSource.connectSource(command)
        }

        refreshDelay.restart()
    }

    Plasma5Support.DataSource {
        id: statusSource

        engine: "executable"
        connectedSources: []

        onNewData: function(sourceName, data) {
            const output = String(data["stdout"] || "").trim()

            if (output === "connected"
                    || output === "connecting"
                    || output === "disconnected") {
                root.vpnState = output
            }

            disconnectSource(sourceName)
        }
    }

    Plasma5Support.DataSource {
        id: actionSource

        engine: "executable"
        connectedSources: []

        onNewData: function(sourceName, data) {
            const standardOutput =
                String(data["stdout"] || "").trim()

            const errorOutput =
                String(data["stderr"] || "").trim()

            if (errorOutput.length > 0) {
                root.lastMessage = errorOutput
            } else if (standardOutput.length > 0) {
                root.lastMessage = standardOutput
            }

            disconnectSource(sourceName)
            refreshDelay.restart()
        }
    }

    Timer {
        interval: 1500
        running: true
        repeat: true
        onTriggered: root.refreshState()
    }

    Timer {
        id: refreshDelay

        interval: 800
        repeat: false
        onTriggered: root.refreshState()
    }

    Component.onCompleted: refreshState()

    compactRepresentation: MouseArea {
        id: compactView

        implicitWidth: Kirigami.Units.iconSizes.smallMedium
        implicitHeight: Kirigami.Units.iconSizes.smallMedium

        hoverEnabled: true

        onClicked: root.expanded = !root.expanded

        Kirigami.Icon {
            anchors.fill: parent
            anchors.margins: 2

            source: "network-vpn"
        }

        Rectangle {
            width: Math.max(8, parent.width * 0.32)
            height: width
            radius: width / 2

            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 1

            color: root.stateColor
            border.width: 1
            border.color: Kirigami.Theme.backgroundColor
        }
    }

    fullRepresentation: Item {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 18
        Layout.preferredWidth: Kirigami.Units.gridUnit * 20

        Layout.minimumHeight: Kirigami.Units.gridUnit * 14
        Layout.preferredHeight: Kirigami.Units.gridUnit * 16

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing

            spacing: Kirigami.Units.largeSpacing

            RowLayout {
                Layout.fillWidth: true

                Kirigami.Icon {
                    source: "network-vpn"

                    Layout.preferredWidth:
                        Kirigami.Units.iconSizes.large

                    Layout.preferredHeight:
                        Kirigami.Units.iconSizes.large
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Kirigami.Heading {
                        text: "UPClink VPN"
                        level: 3
                    }

                    RowLayout {
                        Rectangle {
                            width: 12
                            height: 12
                            radius: 6
                            color: root.stateColor
                        }

                        PlasmaComponents.Label {
                            text: root.stateText
                            font.bold: true
                        }
                    }
                }
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true

                visible: root.vpnState === "connecting"
                text: "Introduce la contraseña en Konsole y después abre la autenticación UPC."
                wrapMode: Text.WordWrap
            }

            PlasmaComponents.Button {
                Layout.fillWidth: true

                text: "Conectar"
                enabled: root.vpnState === "disconnected"

                onClicked: root.runAction("connect")
            }

            PlasmaComponents.Button {
                Layout.fillWidth: true

                text: "Abrir autenticación SSO"
                enabled: root.vpnState === "connecting"

                onClicked: root.runAction("sso")
            }

            PlasmaComponents.Button {
                Layout.fillWidth: true

                text: "Desconectar"
                enabled: root.vpnState !== "disconnected"

                onClicked: root.runAction("disconnect")
            }

            Item {
                Layout.fillHeight: true
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true

                visible: root.lastMessage.length > 0
                text: root.lastMessage
                opacity: 0.7
                wrapMode: Text.WordWrap
            }
        }
    }
}

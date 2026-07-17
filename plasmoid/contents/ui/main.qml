import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support

PlasmoidItem {
    id: root

    property string vpnState: "disconnected"
    property string lastMessage: ""
    property double connectedSince: 0
    property int clockTick: 0

    readonly property string helper:
        "$HOME/.local/bin/upclink-plasma-control"

    readonly property string stateText: {
        switch (vpnState) {
        case "connected":
            return "Conectada"
        case "connecting":
            return "Autenticando"
        case "error":
            return "Error"
        default:
            return "Desconectada"
        }
    }

    readonly property string stateDescription: {
        switch (vpnState) {
        case "connected":
            return "El túnel VPN está activo."
        case "connecting":
            return "Completa la autenticación UPC en el navegador."
        case "error":
            return "No se ha podido completar la operación."
        default:
            return "La conexión VPN no está activa."
        }
    }

    readonly property color stateColor: {
        switch (vpnState) {
        case "connected":
            return "#27ae60"
        case "connecting":
            return "#f1c40f"
        case "error":
            return "#e74c3c"
        default:
            return "#7f8c8d"
        }
    }

    readonly property string elapsedText: {
        clockTick

        if (vpnState !== "connected" || connectedSince === 0) {
            return ""
        }

        const seconds = Math.max(
            0,
            Math.floor((Date.now() - connectedSince) / 1000)
        )

        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        const remainingSeconds = seconds % 60

        const mm = String(minutes).padStart(2, "0")
        const ss = String(remainingSeconds).padStart(2, "0")

        if (hours > 0) {
            return hours + ":" + mm + ":" + ss
        }

        return mm + ":" + ss
    }

    toolTipMainText: "UPClink VPN"
    toolTipSubText: stateText

    Plasmoid.icon: "network-vpn"

    onVpnStateChanged: {
        if (vpnState === "connected" && connectedSince === 0) {
            connectedSince = Date.now()
        } else if (vpnState !== "connected") {
            connectedSince = 0
        }
    }

    function refreshState() {
        const command = helper + " status"

        if (statusSource.connectedSources.indexOf(command) === -1) {
            statusSource.connectSource(command)
        }
    }

    function runAction(actionName) {
        const command = helper + " " + actionName

        lastMessage = ""

        if (actionName === "connect") {
            vpnState = "connecting"
        }

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
                root.vpnState = "error"
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
        interval: 1000
        running: root.vpnState === "connected"
        repeat: true
        onTriggered: root.clockTick++
    }

    Timer {
        id: refreshDelay

        interval: 800
        repeat: false
        onTriggered: root.refreshState()
    }

    Component.onCompleted: refreshState()

    compactRepresentation: MouseArea {
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
        Layout.minimumWidth: Kirigami.Units.gridUnit * 19
        Layout.preferredWidth: Kirigami.Units.gridUnit * 21
        Layout.minimumHeight: Kirigami.Units.gridUnit * 17
        Layout.preferredHeight: Kirigami.Units.gridUnit * 19

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.largeSpacing

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.largeSpacing

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
                        level: 2
                    }

                    PlasmaComponents.Label {
                        text: "Universitat Politècnica de Catalunya"
                        opacity: 0.7
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight:
                    statusLayout.implicitHeight
                    + Kirigami.Units.largeSpacing * 2

                radius: Kirigami.Units.smallSpacing
                color: Kirigami.Theme.backgroundColor
                border.width: 1
                border.color: root.stateColor

                ColumnLayout {
                    id: statusLayout

                    anchors.fill: parent
                    anchors.margins: Kirigami.Units.largeSpacing
                    spacing: Kirigami.Units.smallSpacing

                    RowLayout {
                        Layout.fillWidth: true

                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: root.stateColor
                        }

                        PlasmaComponents.Label {
                            text: root.stateText
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        PlasmaComponents.BusyIndicator {
                            visible: root.vpnState === "connecting"
                            running: visible

                            Layout.preferredWidth:
                                Kirigami.Units.iconSizes.small

                            Layout.preferredHeight:
                                Kirigami.Units.iconSizes.small
                        }
                    }

                    PlasmaComponents.Label {
                        text: root.stateDescription
                        wrapMode: Text.WordWrap
                        opacity: 0.8
                        Layout.fillWidth: true
                    }

                    PlasmaComponents.Label {
                        visible: root.vpnState === "connected"
                        text: "Tiempo conectado: " + root.elapsedText
                        font.bold: true
                    }
                }
            }

            PlasmaComponents.Button {
                Layout.fillWidth: true

                text: "Conectar"
                icon.name: "network-connect"

                visible: root.vpnState === "disconnected"
                         || root.vpnState === "error"

                enabled: visible
                onClicked: root.runAction("connect")
            }

            PlasmaComponents.Button {
                Layout.fillWidth: true

                text: "Abrir autenticación UPC"
                icon.name: "internet-web-browser"

                visible: root.vpnState === "connecting"
                enabled: visible

                onClicked: root.runAction("sso")
            }

            PlasmaComponents.Button {
                Layout.fillWidth: true

                text: "Desconectar"
                icon.name: "network-disconnect"

                visible: root.vpnState === "connecting"
                         || root.vpnState === "connected"

                enabled: visible
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
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}

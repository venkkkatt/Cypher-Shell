import QtQuick 2.15
import QtQuick.Window 2.15
import QtGraphicalEffects 1.15
import CPUMonitor 1.0

Window {
    id: window
    width: 200
    height: 120
    flags: Qt.WindowStaysOnBottomHint | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
    color: "transparent"
    
    // CPU Monitor instance
    CPUMonitor {
        id: cpuMonitor
    }
    
    // Main container
    Rectangle {
        anchors.fill: parent
        color: "#1e1e1e"
        opacity: 0.85
        radius: 12
        border.color: "#333333"
        border.width: 1
        
        // Drop shadow effect
        DropShadow {
            anchors.fill: parent
            horizontalOffset: 0
            verticalOffset: 2
            radius: 8
            samples: 17
            color: "#80000000"
            source: parent
        }
        
        Column {
            anchors.centerIn: parent
            spacing: 8
            
            // CPU label
            Text {
                text: "CPU Usage"
                color: "#ffffff"
                font.family: "monospace"
                font.pixelSize: 14
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            // CPU percentage text
            Text {
                id: cpuText
                text: Math.round(cpuMonitor.cpuUsage) + "%"
                color: getCpuColor(cpuMonitor.cpuUsage)
                font.family: "monospace"
                font.pixelSize: 24
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
                
                function getCpuColor(usage) {
                    if (usage < 30) return "#4ade80"      // Green
                    else if (usage < 60) return "#fbbf24" // Yellow
                    else if (usage < 80) return "#fb923c" // Orange
                    else return "#ef4444"                 // Red
                }
            }
            
            // Progress bar
            Rectangle {
                width: 150
                height: 8
                color: "#333333"
                radius: 4
                anchors.horizontalCenter: parent.horizontalCenter
                
                Rectangle {
                    id: progressBar
                    width: (cpuMonitor.cpuUsage / 100) * parent.width
                    height: parent.height
                    color: cpuText.getCpuColor(cpuMonitor.cpuUsage)
                    radius: 4
                    
                    Behavior on width {
                        NumberAnimation {
                            duration: 300
                            easing.type: Easing.OutQuart
                        }
                    }
                    
                    Behavior on color {
                        ColorAnimation {
                            duration: 300
                        }
                    }
                }
            }
        }
    }
    
    // Pulse animation for high CPU usage
    SequentialAnimation {
        running: cpuMonitor.cpuUsage > 80
        loops: Animation.Infinite
        
        PropertyAnimation {
            target: window
            property: "opacity"
            to: 0.6
            duration: 500
        }
        
        PropertyAnimation {
            target: window
            property: "opacity"
            to: 1.0
            duration: 500
        }
    }
}
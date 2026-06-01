# R550PLUS Three-Omni-Wheel Robot Fault Diagnosis and Desktop Monitoring System

## Project Overview

This project is a graduation design achievement that implements a fault diagnosis system and a desktop monitoring system for the R550PLUS three-omni-wheel mobile robot. The system employs ROS (Robot Operating System) as middleware, combined with a Web remote console and an Electron desktop application, to enable real-time robot state monitoring, fault diagnosis inference, and data management.

### Key Features

- **Omni-directional Motion Control**: Precise motion control for three-omni-wheel robots
- **Real-time Fault Diagnosis**: Offline fault detection using the SAGE-CNN deep learning model
- **Dual-Endpoint Control Architecture**: Complementary design between Web remote console and Electron desktop application
- **Data Acquisition and Management**: Supports collection, labeling, and dataset construction of fault data

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Host System                              │
│  ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │  Web Remote Console │    │   Electron Desktop App     │  │
│  │   (Vite+React)    │    │   (Electron+ONNX Runtime)   │  │
│  └────────┬────────┘    └──────────────┬──────────────┘  │
│           │                            │                 │
│           └──────────┬─────────────────┘                 │
│                      ▼                                   │
│            ┌──────────────────┐                        │
│            │  ROS Master      │                         │
│            │  (rosbridge)    │                         │
│            └────────┬───────┘                        │
└───────────────────┼────────────────────────────────────┘
                    │
┌───────────────────┼────────────────────────────────────┐
│                   ▼         Robot Side System           │
│  ┌──────────────────────────────────────────────────┐ │
│  │              turn_on_wheeltec_robot              │ │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────┐ │ │
│  │  │ Chassis    │  │  IMU Fusion │  │ Current  │ │ │
│  │  │ Controller │  │  Bridge     │  │ Reader   │ │ │
│  │  └────────────┘  └────────────┘  └──────────┘ │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```bash
yp---graduation-design/
├── 01_ROS/                              # ROS Robot Control System
│   ├── turn_on_wheeltec_robot/         # Main Package
│   │   ├── src/                      # C++ Node Source Code
│   │   ├── scripts/                  # Python Scripts
│   │   ├── launch/                   # Launch Files
│   │   ├── params_*/                 # Parameter Configuration Files
│   │   ├── config/                   # Navigation Configuration
│   │   ├── urdf/                    # Robot Model
│   │   ├── web/                     # Web Remote Console
│   │   ├── desktop/                 # Electron Desktop App
│   │   │   ├── renderer/            # Frontend Interface
│   │   │   ├── models/              # Inference Models
│   │   │   └── inference/           # C++ Inference Backend
│   │   └── docs/                    # Development Documentation
│
└── 02 4CH-Current/                   # Four-Channel Current Sensor Firmware
    └── Firmware/                     # STM32 Firmware Source Code
        └── Core/                     # Application Code
```

## Quick Start

### Prerequisites

- Ubuntu 20.04 or later
- ROS Noetic or ROS 2 (choose based on version)
- Node.js 18+
- Python 3.8+

### Build ROS Packages

```bash
cd 01_ROS/turn_on_wheeltec_robot
catkin_make
source devel/setup.bash
```

### Launch the Robot

Recommended three-terminal launch method:

```bash
# Terminal 1: Chassis Control
roslaunch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch

# Terminal 2: Data Collection (Optional)
roslaunch turn_on_wheeltec_robot data_collector.launch

# Terminal 3: Web Control and API (Avoid restarting chassis/collector/current nodes)
roslaunch turn_on_wheeltec_robot web_control.launch
```

### Launch Desktop App

```bash
cd 01_ROS/turn_on_wheeltec_robot/desktop
npm install
npm start
```

## Feature Descriptions

### 1. Motion Control

- **Manual Driving**: Control robot movement via keyboard or virtual joystick
- **Cruise Mode**: Set target speed for autonomous line following
- **Point-and-Orientation Control**: Set target angle for directional control

### 2. Fault Diagnosis

- **Online Inference**: Real-time fault classification based on sensor data
- **Stationary Gating**: Suppress false alarms during stationary states
- **Confidence Voting**: Smooth results across multiple frames

### 3. Data Acquisition

- Sensor data (odometry, IMU, current, battery voltage)
- Fault label annotation
- CSV file storage

### 4. Dataset Construction

- Window slicing generation
- Data normalization
- Train/test set partitioning

## ROS Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/odom` | nav_msgs/Odometry | Odometry data |
| `/imu` | sensor_msgs/Imu | IMU data |
| `/PowerVoltage` | std_msgs/Float32 | Battery voltage |
| `/wheel_speed` | geometry_msgs/Twist | Wheel speed |
| `/cmd_vel` | geometry_msgs/Twist | Control commands |

## Serial Protocols

### Chassis Serial Protocol

- Baud Rate: 115200
- Frame Format: Binary
- Checksum: BCC XOR

### Current Sensor Protocol

- Baud Rate: 9600
- Frame Format: ASCII
- Channels: 4

## Development Documentation

Detailed development documentation is located in `01_ROS/turn_on_wheeltec_robot/docs/`:

- `DESKTOP_APP.md` - Electron Desktop App Development Guide
- `DESKTOP_BUILD_AND_TEST.md` - Build and Test Manual
- `FAULT_INFERENCE.md` - Fault Inference Documentation
- `PROTOCOL.md` - Serial Communication Protocol
- `chapter6_revision.md` - Chapter 6 Thesis Revision

## License

This project is intended solely for academic and research purposes. Do not use it directly in commercial products.
# R550PLUS Three-Omni-Wheel Robot Fault Diagnosis and Desktop Monitoring System

## Project Overview

This project is an undergraduate capstone design that implements a fault diagnosis system and desktop monitoring system for a three-omni-wheel robot based on ROS. The system enables real-time diagnosis of motor eccentricity faults and provides remote monitoring, data collection, and experiment management via an Electron desktop application.

### Main Features

- **Robot Chassis Control**: Differential/omni-wheel robot control based on ROS
- **Fault Diagnosis**: Real-time fault diagnosis using the SAGE-CNN deep learning model
- **Desktop Monitoring**: Electron desktop application for data visualization and control
- **Web Control**: Browser-based experiment control console
- **Data Acquisition**: Multi-channel sensor data collection and CSV storage

## System Components

### 01 ROS

ROS robot control package, including:

- `turn_on_wheeltec_robot/` - Main robot control package
  - C++ nodes: Chassis control, IMU, Heading, current reading, web adapter
  - Python scripts: Data collection, fault injection, web control, serial communication
  - .launch files: Navigation, mapping, data collection
  - Configuration parameters: costmap, TEB planner, navigation
  - URDF models: Multiple robot configurations

- `desktop/` - Electron desktop application
  - Inference backend: ONNX Runtime C++ inference service
  - Desktop application: Main process, render process, database
  - Model files: SAGE-CNN fault classification model

- `web/` - Web console
  - React + Vite frontend
  - Data visualization and experiment management

- `docs/` - Development documentation
  - Protocol specifications, desktop development, fault inference

### 02 4CH-Current

Four-channel current sensor board:

- `Firmware/` - STM32F1xx firmware
  - ADC acquisition of current signals
  - I2C OLED display
  - UART protocol communication

## Quick Start

### Environment Requirements

- Ubuntu 20.04+ / ROS Noetic
- Node.js 18+ (for desktop application)
- Python 3.8+ (for model conversion)
- CMake 3.20+ (for inference program compilation)

### Build

```bash
cd 01\ ROS/turn_on_wheeltec_robot
catkin_make
source devel/setup.bash
```

### Launch

Open three terminals:

**Terminal 1 - Chassis Control**
```bash
roslaunch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch
```

**Terminal 2 - Data Collection**
```bash
roslaunch turn_on_wheeltec_robot data_collector.launch
```

**Terminal 3 - Web Control**
```bash
roslaunch turn_on_wheeltec_robot web_control.launch
```

### Launch Desktop Application

```bash
cd 01\ ROS/turn_on_wheeltec_robot/desktop
npm install
npm start
```

## Core Topics

### Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/odom` | nav_msgs/Odometry | Odometry data |
| `/imu` | sensor_msgs/Imu | IMU data |
| `/heading` | std_msgs/Float32 | Heading angle |
| `/wheel_speed` | geometry_msgs/Twist | Wheel speeds |
| `/PowerVoltage` | std_msgs/Float32 | Battery voltage |
| `/current` | sensor_msgs/JointState | Current readings |

### Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | geometry_msgs/Twist | Velocity command |
| `/cruise_cmd` | geometry_msgs/Twist | Cruise command |
| `/cruise_enable` | std_msgs/Bool | Cruise enable |
| `/web/estop` | std_msgs/Bool | Emergency stop |

## Fault Diagnosis

### Model Input

- 16-channel sensor data
- Sliding window: 20 time steps
- Normalization: StandardScaler

### Output Labels

- `normal_static` - Normal stationary
- `normal_moving` - Normal moving
- `eccentricity_a` - Wheel A eccentricity
- `eccentricity_b` - Wheel B eccentricity
- `eccentricity_c` - Wheel C eccentricity
- `eccentricity_d` - Wheel D eccentricity
- `brake` - Brake fault

### Diagnosis Logic

1. **Stationary gating**: Suppresses false "normal moving" reports when velocity is below threshold
2. **Confidence voting**: Fault is confirmed only after multiple consecutive high-confidence predictions
3. **Latching mechanism**: Alarm state remains active after fault detection

## Data Collection

### Collection Commands

```bash
rostopic pub /data_collector/enable std_msgs/Bool "data: true" -1
rostopic pub /data_collector/config turn_on_wheeltec_robot/CollectorConfig "{fault_label: 'eccentricity_a', motion_mode: 'straight'}" -1
```

### Output Format

CSV files contain: timestamp, 16-channel sensor data, fault label

## Serial Protocols

### Chassis Serial

- Baud rate: 115200
- Protocol: Binary, custom frame format
- Checksum: BCC XOR

### Current Sensor Serial

- Baud rate: 9600
- Protocol: ASCII text
- Format: `$CH1,CH2,CH3,CH4,CHECKSUM\r\n`

## Directory Structure

```
01 ROS/
├── turn_on_wheeltec_robot/
│   ├── src/           # C++ node source code
│   ├── scripts/      # Python scripts
│   ├── launch/       # Launch files
│   ├── config/      # Configuration files
│   ├── params_*/    # Navigation parameters
│   ├── urdf/        # Robot models
│   ├── include/     # Header files
│   ├── desktop/     # Electron desktop application
│   │   ├── models/  # Model files
│   │   ├── inference/ # Inference backend
│   │   └── renderer/ # Frontend interface
│   ├── web/         # Web console
│   ├── docs/        # Development documentation
│   └── map/         # Map files

02 4CH-Current/
├── Firmware/         # STM32 firmware
├── HostApp/         # Host application
└── ROS/            # ROS nodes
```

## License

MIT License

## Author

Capstone Project - Robot Fault Diagnosis and Monitoring System
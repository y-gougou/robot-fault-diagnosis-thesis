# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository is the complete codebase for a Yanshan University undergraduate graduation design project built around the **WHEELTEC R550PLUS three-omnidirectional-wheel robot**. It consists of four sub-projects spanning embedded firmware, ROS middleware, Web/desktop monitoring, and deep-learning fault diagnosis.

| Directory | Name | Stack |
|-----------|------|-------|
| `01_ROS/turn_on_wheeltec_robot` | ROS robot control & data collection | ROS1 Noetic, C++14, Python 3, catkin, React, Vite, Electron, ONNX Runtime |
| `02 4CH-Current/` | 4-channel current sensor system | STM32F103 (HAL), Keil/EIDE, Python 3.10+, PySide6, ROS Noetic |
| `03 omi_car/` | Omnidirectional wheel chassis firmware | STM32F4 (SPL), FreeRTOS v9.0.0, EIDE/Keil AC5 |
| `04 last dance/last dance/ypmodel/` | Fault diagnosis deep learning | Python 3.11, PyTorch, ONNX |

## Common Commands

### 01 ROS — `turn_on_wheeltec_robot`

```bash
# C++ nodes (from catkin workspace root)
catkin_make && source devel/setup.bash

# Launch chassis + IMU + odometry
roslaunch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch

# Launch full web control stack (chassis + web server + rosbridge + collector)
roslaunch turn_on_wheeltec_robot web_control.launch

# Data collection with fault label
roslaunch turn_on_wheeltec_robot data_collector.launch fault_label:=0

# Disable conflicting modules when running partial stacks
roslaunch turn_on_wheeltec_robot web_control.launch \
  start_base:=false start_current_reader:=false start_data_collector:=false
```

**Web frontend** (`01_ROS/turn_on_wheeltec_robot/web/`):
```bash
cd 01_ROS/turn_on_wheeltec_robot/web
npm run build          # Production build to web/dist/
npm run dev            # Dev server on :5173
```

**Electron desktop** (`01_ROS/turn_on_wheeltec_robot/desktop/`):
```bash
cd 01_ROS/turn_on_wheeltec_robot/desktop
npm run setup:env      # First-time: download toolchain, create Python venv
npm start              # Dev mode
npm run build:infer    # Compile C++ ONNX Runtime inference backend
npm run build:win      # Build Windows installer (slow; use :dir for unpacked)
npm run build:win:dir  # Fast unpacked directory build
npm run export:model   # Export trained SAGE-CNN to ONNX model package
```

### 02 4CH-Current

```bash
# Firmware: open Firmware/MDK-ARM/*.uvprojx in Keil MDK-ARM, or use EIDE in VS Code

# HostApp (uv-managed Python)
cd "02 4CH-Current/HostApp"
uv sync
uv run ch4-current       # Run GUI
uv run black src/        # Format
uv run ruff check src/   # Lint
uv run mypy src/         # Type check

# ROS driver
catkin_make
roslaunch ch4_current_sensor sensor.launch port:=/dev/ttyUSB0 baudrate:=115200

# Calibration tool
cd "02 4CH-Current/Tools"
pip install -r requirements.txt
python calibration_tool.py
```

### 03 omi_car

Build via **VS Code + EIDE extension** or **Keil MDK-ARM**. VS Code tasks: `build`, `flash`, `build and flash`, `clean`. Clean Keil artifacts with `keilkilll.bat`.

Compiler: AC5, C99, optimization level 2, hardware FPU, microLIB.

### 04 last dance

```bash
cd "04 last dance/last dance/ypmodel"

# Three-phase experiment pipeline
python run_experiments.py --mode paper_main_vx05 --require_figures
python run_experiments.py --mode paper_generalization --main_results results_paper_main_vx05 --require_figures
python run_experiments.py --mode deployment_robust --require_figures

# Quick smoke test
python run_experiments.py --mode paper_main_vx05 --smoke --output_dir results_smoke --require_figures

# Replay inference on a single CSV
python replay_inference.py --csv ../shuju0517/normal/xxx.csv \
  --model results_deployment_robust/export/best_model.onnx
```

## High-Level Architecture

### Cross-Project Data Flow

The system has a clear bottom-up pipeline:

```
03 omi_car (STM32F4 firmware)
    │ serial 115200
    ▼
01 ROS wheeltec_robot_node
    │ publishes /odom, /imu, /wheel_speed, /PowerVoltage
    ▼
02 4CH-Current sensor board
    │ serial 115200 → publishes /current_data
    ▼
01 ROS data_collector.py
    │ time-sync → CSV 16-channel log
    ▼
04 last dance (preprocess + train)
    │ sliding window [15, 50] → SAGE-CNN → ONNX export
    ▼
01 ROS desktop Electron + C++ ONNX Runtime inference
```

### Chassis Serial Protocol (ROS ↔ STM32)

A custom binary protocol over `/dev/ttyCH343USB0` at 115200 baud.

- **ROS → STM32**: 13-byte frame. Byte 2 is the `angle_flag`: `0`=speed, `1`=target angle, `2`=reset angle, `3`=external heading. Speeds are `int16` big-endian in mm/s or mrad/s; angle is `int16` big-endian in 0.1°. BCC XOR checksum over bytes 0–10; byte 12 is `0x7D`.
- **STM32 → ROS**: 30-byte frame with velocities, accelerometer, gyroscope, voltage, and three wheel speeds. BCC XOR over bytes 0–27.

Key source pairs to keep in sync:
- ROS send: `src/wheeltec_robot.cpp` (`Send_Chassis_Command()`)
- ROS receive: `src/wheeltec_robot.cpp` (`Get_Sensor_Data_New()`)
- STM32 send: `03 omi_car/HARDWARE/usartx.c` (`data_transition()`)
- STM32 receive: `03 omi_car/HARDWARE/usartx.c` (`USART3_IRQHandler()`)

> **IMU axis remapping happens in firmware before transmission** (`usartx.c`): raw MPU6050 Y→X, raw X (inverted)→Y. ROS receives already-transformed data.

### Command Architecture

The system deliberately separates **speed commands** from **heading target commands**.

**Speed path:**
```
Web frontend → /cmd_vel_web → cmd_vel_web_adapter.py → /cmd_vel → wheeltec_robot_node → STM32
```

**Heading target path (independent):**
```
/target_angle        (std_msgs/Float32, degrees)
/target_angle_reset  (std_msgs/Empty)
/web/heading_zero    (std_msgs/Empty)
```

Cruise control publishes `/web/cruise_cmd` + `/web/cruise_enable`; the adapter applies PID on `linear.x/y` but intentionally leaves `angular.z = 0`, relying on the STM32 internal angle loop for heading hold.

### Web Control Safety Layer

`cmd_vel_web_adapter.py` (and its C++ counterpart) is safety-critical:
- Heartbeat timeout: 1.0s → emergency stop latch
- Command timeout: 0.5s → zero velocity
- Speed limits: X 1.50 m/s, Y 1.00 m/s, Z 3.75 rad/s
- Dead zones: linear 0.02, angular 0.03

Any change to timeouts, limits, or dead zones must be validated on hardware before deployment.

### N100 IMU Heading Standardization

```
/n100/imu (sensor_msgs/Imu)
  → heading_bridge.py
  → /chassis/heading_deg (std_msgs/Float32, degrees, unwrapped, zero-offset)
  → wheeltec_robot_node
  → STM32 external heading frame (angle_flag=3)
```

Enable with `start_fdilink_ahrs:=true` in launch files.

### Desktop Fault Inference Architecture

The Electron app spawns a C++ JSON-RPC subprocess (`yp_fault_infer`) that loads an ONNX model and runs inference on a sliding 50-point, 15-channel sensor window.

```
Robot rosbridge → Electron Renderer → Main (IPC) → yp_fault_infer (C++)
                                                         ↓
                                               ONNX Runtime backend
                                                         ↓
                                               model_manifest.json + scaler.json
```

Feature order (fixed):
`odom_vx, odom_vy, odom_wz, wheel_speed0, wheel_speed1, wheel_speed2, imu_ax, imu_ay, imu_az, imu_gx, imu_gy, imu_gz, current0, current1, current2`

Window rules: size 50, step 10, shape `[1, 15, 50]`. `/wheel_speed` is mandatory; the UI will not pad zeros silently.

### 02 4CH-Current Protocol Mismatch

The firmware default uses **FireWater text protocol** (`$CURRENT,ch0,ch1,ch2*XX\r\n`), but `HostApp/protocol.py` and `ROS/scripts/sensor_node.py` only implement the **binary protocol**. Before host/ROS integration, set `UART_PROTOCOL_TYPE` in `Firmware/Core/Inc/uart_protocol.h` to match both sides.

### 04 last dance Experiment Pipeline

1. **Preprocess**: `preprocess_fault_dataset.py` reads CSVs from `../shuju0517`, applies sliding window (50, step 10), trims 5s head/tail, stratified split, and `StandardScaler` fit only on train.
2. **Train**: `run_experiments.py` runs three phases (main vx=0.5, cross-speed generalization, deployment robustness) with fixed random seeds per run.
3. **Export**: `desktop/inference/tools/export_sage_cnn_onnx.py` converts the best `.pth` + `strict_scaler.pkl` into an ONNX model package for the desktop app.

Label mapping in unified experiments: `0 normal`, `1 wheel_slip`, `2 drive_abnormal`, `3 shaft_eccentricity`.

## Important Notes

- **03 omi_car** has a `CONTROL_DELAY` of ~10 seconds before motion is allowed. Do not shorten without understanding IMU warmup requirements.
- **File case sensitivity**: `03 omi_car` has mixed-case filenames (e.g., `LED.C` vs `led.h`). Preserve exact casing when editing.
- **Global state in 03**: Nearly all important variables are declared `extern` in `BALANCE/system.h` and defined in `BALANCE/system.c`.
- **Dataset path hardcoding**: `/home/wheeltec/R550PLUS_data_collect/log_v2` is the default collector output. Sync path changes across `data_collector.launch`, `web_dashboard_server.py`, and desktop config.
- **ROS topic constants** are centralized in `desktop/renderer/topics.js` and `web/src/` constants. Keep them aligned when adding or renaming topics.

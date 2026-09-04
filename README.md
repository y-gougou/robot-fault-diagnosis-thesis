

# R550PLUS 三全向轮机器人故障诊断与桌面监控系统

## 项目概述

本项目为本科毕业设计，实现了基于 ROS 的三全向轮机器人故障诊断系统与桌面监控系统。系统可以对机器人电机偏心故障进行实时诊断，并通过 Electron 桌面端实现远程监控、数据采集和实验管理。

### 主要功能

- **机器人底盘控制**：基于 ROS 的差速/全向轮机器人控制
- **故障诊断**：基于 SAGE-CNN 深度学习模型的实时故障诊断
- **桌面监控**：Electron 桌面端应用，实现数据可视化与控制
- **Web 控制**：浏览器端的实验控制台
- **数据采集**：多通道传感器数据采集与 CSV 存储

## 系统组成

### 01 ROS

ROS 机器人控制包，包含：

- `turn_on_wheeltec_robot/` - 机器人控制主包
  - C++ 节点：底盘控制、IMU、Heading、电流读取、Web适配器
  - Python 脚本：数据采集、故障注入、Web控制、串口通信
  - .launch 启动文件：导航、建图、数据采集
  - 配置参数：costmap、TEB planner、navigation
  - URDF 模型：多种机器人配置

- `desktop/` - Electron 桌面端
  - 推理后端：ONNX Runtime C++ 推理服务
  - 桌面应用：主进程、渲染进程、数据库
  - 模型文件：SAGE-CNN 故障分类模型

- `web/` - Web 控制台
  - React + Vite 前端
  - 数据可视化、实验管理

- `docs/` - 开发文档
  - 协议说明、桌面端开发、故障推理

### 02 4CH-Current

四通道电流传感器板:

- `Firmware/` - STM32F1xx 固件
  - ADC 采集电流信号
  - I2C OLED 显示
  - UART 协议通信

## 快速开始

### 环境要求

- Ubuntu 20.04+ / ROS Noetic
- Node.js 18+ (桌面端)
- Python 3.8+ (模型转换)
- CMake 3.20+ (推理程序编译)

### 编译

```bash
cd 01\ ROS/turn_on_wheeltec_robot
catkin_make
source devel/setup.bash
```

### 启动

需要打开三个终端：

**终端 1 - 底盘控制**
```bash
roslaunch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch
```

**终端 2 - 数据采集**
```bash
roslaunch turn_on_wheeltec_robot data_collector.launch
```

**终端 3 - Web 控制**
```bash
roslaunch turn_on_wheeltec_robot web_control.launch
```

### 桌面端启动

```bash
cd 01\ ROS/turn_on_wheeltec_robot/desktop
npm install
npm start
```

## 核心话题

### 发布

| 话题 | 类型 | 说明 |
|------|------|------|
| `/odom` | nav_msgs/Odometry | 里程计 |
| `/imu` | sensor_msgs/Imu | IMU 数据 |
| `/heading` | std_msgs/Float32 | 航向角 |
| `/wheel_speed` | geometry_msgs/Twist | 轮速 |
| `/PowerVoltage` | std_msgs/Float32 | 电池电压 |
| `/current` | sensor_msgs/JointState | 电流 |

### 订阅

| 话题 | 类型 | 说明 |
|------|------|------|
| `/cmd_vel` | geometry_msgs/Twist | 速度指令 |
| `/cruise_cmd` | geometry_msgs/Twist | 巡航指令 |
| `/cruise_enable` | std_msgs/Bool | 巡航使能 |
| `/web/estop` | std_msgs/Bool | 急停 |

## 故障诊断

### 模型输入

- 16 通道传感器数据
- 滑动窗口：20 个时间步
- 归一化：StandardScaler

### 输出标签

- `normal_static` - 正常静止
- `normal_moving` - 正常运动
- `eccentricity_a` - A轮偏心
- `eccentricity_b` - B轮偏心
- `eccentricity_c` - C轮偏心
- `eccentricity_d` - D轮偏心
- `brake` - 刹车故障

### 诊断逻辑

1. 静止门控：速度低于阈值时抑制正常运动误报
2. 置信度投票：连续多次高置信度触发才确认
3. 锁存机制：故障发生后保持报警状态

## 数据采集

### 采集命令

```bash
rostopic pub /data_collector/enable std_msgs/Bool "data: true" -1
rostopic pub /data_collector/config turn_on_wheeltec_robot/CollectorConfig "{fault_label: 'eccentricity_a', motion_mode: 'straight'}" -1
```

### 输出格式

CSV 文件包含：时间戳、16通道传感器数据、故障标签

## 串口协议

### 底盘串口

- 波特率：115200
- 协议：二进制，自定义帧格式
- 校验：BCC XOR

### 电流串口

- 波特率：9600
- 协议：ASCII 文本
- 格式：`$CH1,CH2,CH3,CH4,CHECKSUM\r\n`

## 目录结构

```
01 ROS/
├── turn_on_wheeltec_robot/
│   ├── src/           # C++ 节点源码
│   ├── scripts/      # Python 脚本
│   ├── launch/       # 启动文件
│   ├── config/      # 配置文件
│   ├── params_*/    # 导航参数
│   ├── urdf/        # 机器人模型
│   ├── include/     # 头文件
│   ├── desktop/     # Electron 桌面端
│   │   ├── models/  # 模型文件
│   │   ├── inference/ # 推理后端
│   │   └── renderer/ # 前端界面
│   ├── web/         # Web 控制台
│   ├── docs/        # 开发文档
│   └── map/         # 地图文件

02 4CH-Current/
├── Firmware/         # STM32 固件
├── HostApp/         # 上位机程序
└── ROS/            # ROS 节点
```

## 许可证

MIT License

## 作者

毕业设计 - 机器人故障诊断与监控系统
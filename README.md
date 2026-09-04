

# R550PLUS 三全向轮机器人故障诊断与桌面监控系统

## 项目简介

本项目为毕业设计成果，实现了基于 R550PLUS 三全向轮移动机器人的故障诊断系统与桌面监控系统。该系统采用 ROS（Robot Operating System）作为中间件，结合 Web 远程控制台和 Electron 桌面端应用，实现了机器人的实时状态监控、故障诊断推理和数据管理功能。

### 主要特性

- **全向移动控制**：支持三全向轮（Omni Wheel）机器人的精确运动控制
- **实时故障诊断**：基于 SAGE-CNN 深度学习模型的离线推理故障检测
- **双端控制架构**：Web 远程控制台与 Electron 桌面端互补设计
- **数据采集与管理**：，支持故障数据的采集、标注和数据集构建

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    上位机系统                              │
│  ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │  Web 远程控制台  │    │   Electron 桌面端           │  │
│  │   (Vite+React)  │    │   (Electron+ONNX Runtime)   │  │
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
│                   ▼         机器人侧系统                │
│  ┌──────────────────────────────────────────────────┐ │
│  │              turn_on_wheeltec_robot              │ │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────┐ │ │
│  │  │ 底盘控制   │  │  IMU融合   │  │ 电流读取 │ │ │
│  │  │  Node      │  │  Bridge   │  │  Reader │ │ │
│  │  └────────────┘  └────────────┘  └──────────┘ │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 目录结构

```bash
yp---graduation-design/
├── 01_ROS/                              # ROS 机器人控制系统
│   ├── turn_on_wheeltec_robot/         # 主功能包
│   │   ├── src/                      # C++ 节点源码
│   │   ├── scripts/                  # Python 脚本
│   │   ├── launch/                   # 启动文件
│   │   ├── params_*/                 # 参数配置文件
│   │   ├── config/                   # 导航配置
│   │   ├── urdf/                    # 机器人模型
│   │   ├── web/                     # Web 远程控制台
│   │   ├── desktop/                 # Electron 桌面端
│   │   │   ├── renderer/            # 前端界面
│   │   │   ├── models/              # 推理模型
│   │   │   └── inference/           # C++ 推理后端
│   │   └── docs/                    # 开发文档
│
└── 02 4CH-Current/                   # 四路电流传感器固件
    └── Firmware/                     # STM32 固件源码
        └── Core/                     # 应用代码
```

## 快速开始

### 环境要求

- Ubuntu 20.04 或更高版本
- ROS Noetic 或 ROS 2（根据版本选择）
- Node.js 18+
- Python 3.8+

### 编译 ROS 包

```bash
cd 01_ROS/turn_on_wheeltec_robot
catkin_make
source devel/setup.bash
```

### 启动机器人

推荐三终端启动方式：

```bash
# 终端 1：底盘控制
roslaunch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch

# 终端 2：数据采集（可选）
roslaunch turn_on_wheeltec_robot data_collector.launch

# 终端 3：Web 控制与 API（避免重复启动底盘/采集/电流节点）
roslaunch turn_on_wheeltec_robot web_control.launch
```

### 启动桌面端

```bash
cd 01_ROS/turn_on_wheeltec_robot/desktop
npm install
npm start
```

## 功能说明

### 1. 运动控制

- **手动驾驶**：通过键盘或虚拟摇杆控制机器人运动
- **巡航模式**：设定目标速度自主巡线
- **定点定向**：设定目标角度进行方向控制

### 2. 故障诊断

- **在线推理**：基于实时传感器数据的故障分类
- **静止门控**：抑制静止状态下的误报
- **置信度投票**：多帧结果平滑处理

### 3. 数据采集

- 传感器数据（里程计、IMU、电流、电量）
- 故障标签标注
- CSV 文件存储

### 4. 数据集构建

- Window 切片生成
- 数据标准化
- 训练/测试集划分

## ROS 话题

| 话题 | 类型 | 说明 |
|-----|------|------|
| `/odom` | nav_msgs/Odometry | 里程计数据 |
| `/imu` | sensor_msgs/Imu | IMU 数据 |
| `/PowerVoltage` | std_msgs/Float32 | 电池电压 |
| `/wheel_speed` | geometry_msgs/Twist | 车轮速度 |
| `/cmd_vel` | geometry_msgs/Twist | 控制指令 |

## 串口协议

### 底盘串口协议

- 波特率：115200
- 数据帧：二进制格式
- 校验：BCC XOR

### 电流传感器协议

- 波特率：9600
- 数据帧：ASCII 格式
- 通道数：4

## 开发文档

详细开发文档位于 `01_ROS/turn_on_wheeltec_robot/docs/` 目录：

- `DESKTOP_APP.md` - Electron 桌面端开发文档
- `DESKTOP_BUILD_AND_TEST.md` - 构建与测试手册
- `FAULT_INFERENCE.md` - 故障推理文档
- `PROTOCOL.md` - 串口通信协议
- `chapter6_revision.md` - 第六章论文修订

## 许可证

本项目仅供学习研究使用，请勿直接用于商业产品。
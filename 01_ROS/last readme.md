# R550PLUS 三全向轮机器人故障诊断与桌面监控系统最终说明文档

本文档是本工程的最终汇总说明，面向毕业设计答辩、工程复现、后续维护和现场演示。内容覆盖 ROS 底盘控制、传感器采集、Web 控制、Electron 桌面端、故障诊断推理、模型替换、报警逻辑、数据集构建、运行测试与常见问题。

工程根目录：

```text
D:\projects\01 ROS
```

ROS 包目录：

```text
D:\projects\01 ROS\turn_on_wheeltec_robot
```

## 1. 项目总体目标

本项目围绕 R550PLUS 三全向轮移动机器人，完成一套集成式机器人状态监控、数据采集、故障注入、故障诊断和桌面端交互系统。系统主要目标包括：

- 实现机器人底盘串口通信，接收里程计、IMU、电池电压等底盘数据。
- 采集多源传感器数据，包括里程计、IMU、三路轮速、三路电流和控制命令。
- 提供 Web 控制和 Electron 桌面端控制界面。
- 支持手动驾驶、急停、定速巡航、航向角控制和实验流程管理。
- 支持故障注入实验，包括正常、打滑、驱动异常、电机轴偏心等状态。
- 将训练完成的 SAGE-CNN 故障诊断模型导出为 ONNX 模型包。
- 在桌面端实时聚合 15 通道传感器窗口，调用 C++ ONNX Runtime 推理程序完成故障识别。
- 提供静止门控、置信度门控、投票稳定和故障报警锁存，降低误报。
- 形成可复现的数据采集、模型导出、桌面端加载和故障报警流程。

## 2. 系统组成

本工程由五个主要部分组成：

| 子系统 | 位置 | 说明 |
| --- | --- | --- |
| ROS 底盘节点 | `turn_on_wheeltec_robot/src` | C++ 节点，负责底盘串口通信、速度下发、里程计和 IMU 发布。 |
| ROS 辅助节点 | `turn_on_wheeltec_robot/scripts` | 数据采集、Web API、故障注入、标记发送等 Python 节点。 |
| Web 控制端 | `turn_on_wheeltec_robot/web` | 浏览器控制界面，基于 rosbridge 与机器人通信。 |
| Electron 桌面端 | `turn_on_wheeltec_robot/desktop` | 桌面应用，集成监控、控制、采集、实验和故障诊断。 |
| 故障诊断后端 | `desktop/inference/onnxruntime` | C++ JSON-RPC 推理进程，加载 ONNX 模型并执行后处理。 |

总体数据流如下：

```text
机器人底盘 STM32
  <-> wheeltec_robot_node
  -> /odom /imu /PowerVoltage /wheel_speed

电流传感器
  -> current_reader_node 或 current_reader.py
  -> /current_data

rosbridge_websocket
  <-> Web 前端 / Electron 桌面端

Electron 桌面端
  -> 聚合 50x15 实时窗口
  -> yp_fault_infer.exe
  -> ONNX Runtime
  -> 故障类别、置信度、报警状态
```

## 3. 目录结构说明

核心目录如下：

```text
turn_on_wheeltec_robot/
├── src/                         # C++ ROS 节点
├── include/                     # C++ 头文件
├── scripts/                     # Python ROS 节点和工具
├── launch/                      # ROS 启动文件
├── config/                      # 导航与规划参数
├── map/                         # 地图文件
├── web/                         # 浏览器 Web 控制端
├── desktop/                     # Electron 桌面端
├── docs/                        # 专项文档
├── CMakeLists.txt               # catkin 构建配置
└── package.xml                  # ROS 包依赖声明
```

重要文档：

| 文档 | 用途 |
| --- | --- |
| `README.md` | ROS 包与桌面端概要说明。 |
| `docs/DESKTOP_APP.md` | Electron 桌面端详细说明。 |
| `docs/DESKTOP_BUILD_AND_TEST.md` | 桌面端环境准备、测试和打包流程。 |
| `docs/FAULT_INFERENCE.md` | 故障诊断推理、模型包和 ONNX Runtime 文档。 |
| `docs/PROTOCOL.md` | 串口协议说明。 |
| `docs/代码实现说明.md` | 代码实现细节说明。 |

## 4. ROS 编译与基础环境

### 4.1 ROS 依赖

ROS 包依赖主要包括：

- `roscpp`
- `rospy`
- `geometry_msgs`
- `nav_msgs`
- `sensor_msgs`
- `std_msgs`
- `tf`
- `serial`
- `rosbridge_server`

`package.xml` 中已声明依赖。

### 4.2 编译命令

在机器人侧 catkin 工作空间中编译：

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

如果只修改 Python 脚本、Web 前端或桌面端，不需要重新 `catkin_make`。

如果修改以下内容，需要重新编译：

- `src/` 下 C++ 源码。
- `include/` 下 C++ 头文件。
- `CMakeLists.txt`。

### 4.3 当前 C++ 节点

`CMakeLists.txt` 当前编译以下节点：

| 节点 | 源码 | 功能 |
| --- | --- | --- |
| `wheeltec_robot_node` | `src/wheeltec_robot.cpp` | 底盘串口通信、速度控制、里程计、IMU、电压发布。 |
| `heading_bridge_node` | `src/heading_bridge_node.cpp` | 航向桥接。 |
| `cmd_vel_web_adapter_node` | `src/cmd_vel_web_adapter_node.cpp` | Web 控制安全适配器。 |
| `current_reader_node` | `src/current_reader_node.cpp` | 电流传感器读取。 |

## 5. 机器人侧启动方式

### 5.1 推荐三终端启动方式

当同时使用底盘控制、数据采集和桌面端/Web 控制时，推荐分开启动，避免重复启动底盘或采集节点。

终端 1：底盘控制

```bash
roslaunch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch
```

终端 2：数据采集

```bash
roslaunch turn_on_wheeltec_robot data_collector.launch fault_label:=0
```

终端 3：Web 控制与 API

```bash
roslaunch turn_on_wheeltec_robot web_control.launch \
  start_base:=false \
  start_current_reader:=false \
  start_data_collector:=false
```

### 5.2 一键 Web 控制启动

如果希望由 `web_control.launch` 启动更多组件：

```bash
roslaunch turn_on_wheeltec_robot web_control.launch
```

它通常会启动：

- rosbridge WebSocket。
- Web 页面服务。
- Web 控制安全适配器。
- 底盘控制节点。
- 电流读取节点。
- 数据采集节点。

具体是否启动由 launch 参数控制。

### 5.3 常用端口

| 服务 | 地址 | 说明 |
| --- | --- | --- |
| Web 页面 | `http://<robot_ip>:8000` | 浏览器控制台和 HTTP API。 |
| rosbridge | `ws://<robot_ip>:9090` | WebSocket ROS 桥接。 |

桌面端连接时需要填写机器人 IP，例如：

```text
172.20.10.6
```

桌面端会自动连接：

```text
ws://172.20.10.6:9090
http://172.20.10.6:8000
```

## 6. 串口设备与协议

### 6.1 串口设备

| 设备 | 默认路径 | 波特率 | 用途 |
| --- | --- | ---: | --- |
| 底盘控制器 | `/dev/ttyCH343USB0` | 115200 | 电机控制、里程计、IMU、电压。 |
| 电流传感器 | `/dev/ttyUSB0` 或 `/dev/ttyUSB1` | 115200 | 三通道电流。 |

现场调试时先检查：

```bash
ls -l /dev/ttyCH343USB0 /dev/ttyUSB0 /dev/ttyUSB1
```

### 6.2 底盘串口协议

底盘数据帧：

- 帧头：`0x7B`
- 帧尾：`0x7D`
- 校验：BCC

速度指令：

- `linear.x`
- `linear.y`
- `angular.z`

三者各占 2 字节，单位通常为 mm/s 或协议内部单位。

### 6.3 电流传感器协议

电流帧格式：

```text
$CURRENT,ch0,ch1,ch2*XX\r\n
```

或带序号：

```text
$CURRENT,seq,ch0,ch1,ch2*XX\r\n
```

`XX` 为 XOR 校验。

## 7. 核心 ROS 话题

| 话题 | 类型 | 频率 | 说明 |
| --- | --- | ---: | --- |
| `/odom` | `nav_msgs/Odometry` | 约 20 Hz | 位置、速度、姿态。 |
| `/imu` | `sensor_msgs/Imu` | 约 20 Hz | IMU 数据。 |
| `/PowerVoltage` | `std_msgs/Float32` | 约 20 Hz | 电池电压。 |
| `/wheel_speed` | `std_msgs/Float32MultiArray` | 约 20 Hz | 三路轮速，故障诊断必需。 |
| `/current_data` | `std_msgs/Float32MultiArray` | 约 5-6 Hz | 三路电流。 |
| `/cmd_vel_web` | `geometry_msgs/Twist` | 实时 | Web/桌面端原始控制命令。 |
| `/cmd_vel` | `geometry_msgs/Twist` | 约 40 Hz | 安全适配后的最终底盘速度。 |
| `/web/heartbeat` | `std_msgs/Empty` | 周期 | Web/桌面端心跳。 |
| `/web/estop` | `std_msgs/Bool` | 事件 | 急停控制。 |
| `/web/cruise_cmd` | `geometry_msgs/Twist` | 事件 | 巡航目标速度。 |
| `/web/cruise_enable` | `std_msgs/Bool` | 事件 | 巡航开关。 |
| `/web/control_status` | `std_msgs/String` | 状态 | Web 控制适配器状态。 |
| `/web/collection_config` | `std_msgs/String` | 事件 | 数据采集配置。 |
| `/web/collection_enable` | `std_msgs/Bool` | 事件 | 数据采集启停。 |
| `/web/collection_status` | `std_msgs/String` | 状态 | 数据采集状态。 |

## 8. Web 控制安全层

Web/桌面端并不直接控制底盘节点，而是先发布到：

```text
/cmd_vel_web
```

安全适配器再发布：

```text
/cmd_vel
```

安全适配器负责：

- 心跳检测。
- 指令超时停机。
- 急停锁存。
- 最大速度限制。
- 死区处理。
- 巡航模式 PID 修正。
- 控制状态发布。

关键安全参数：

| 参数 | 默认值 | 说明 |
| --- | ---: | --- |
| `cmd_timeout` | 0.5 s | 控制指令超时停机。 |
| `heartbeat_timeout` | 1.0 s | 心跳超时停机。 |
| `max_linear_x` | 1.50 m/s | X 方向最大线速度。 |
| `max_linear_y` | 1.00 m/s | Y 方向最大线速度。 |
| `max_angular_z` | 3.75 rad/s | 最大角速度。 |
| `linear_deadband` | 0.02 | 线速度死区。 |
| `angular_deadband` | 0.03 | 角速度死区。 |

## 9. Electron 桌面端

### 9.1 目录

桌面端位于：

```text
turn_on_wheeltec_robot/desktop
```

主要文件：

| 文件 | 说明 |
| --- | --- |
| `main.js` | Electron 主进程，创建窗口并注册 IPC。 |
| `preload.js` | 安全暴露 `window.electronAPI`。 |
| `renderer/app.js` | 页面状态、ROS 订阅、控制、推理和报警逻辑。 |
| `renderer/index.html` | 页面结构。 |
| `renderer/styles.css` | 页面布局和样式。 |
| `renderer/topics.js` | ROS topic 常量。 |
| `renderer/ros-client.js` | rosbridge WebSocket 客户端。 |
| `inference-service.js` | C++ 推理子进程管理。 |
| `model-converter-service.js` | 模型转换服务。 |
| `db/database.js` | 本地 SQLite 数据库。 |
| `models/sage_cnn` | 默认故障诊断模型包。 |

### 9.2 环境准备

首次使用：

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop"
npm install
```

如果需要准备完整推理/打包环境：

```powershell
npm run setup:env
```

该命令会准备：

- Node/Electron 依赖。
- 本地 Python 环境。
- 模型导出依赖。
- CMake、Ninja 等构建工具。

### 9.3 启动桌面端

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop"
npm start
```

启动后在连接区域填写机器人 IP，例如：

```text
172.20.10.6
```

点击连接后，桌面端通过 rosbridge 订阅实时数据，并通过 HTTP API 获取 CSV 和数据集信息。

### 9.4 桌面端功能

桌面端当前包含：

- 连接状态显示。
- ROS 实时状态监控。
- 速度、电流、IMU、航向图表。
- 手动驾驶。
- 急停与停止。
- 定速巡航。
- 航向角控制。
- 数据采集控制。
- CSV 文件列表和预览。
- 数据集构建入口。
- 实验向导与故障注入。
- 故障诊断推理。
- 故障报警锁存。
- 主题、语言、字体、字号、背景图设置。
- 本地连接历史和实验记录。

## 10. 桌面端故障诊断

### 10.1 推理架构

桌面端故障诊断链路如下：

```text
ROS 实时话题
  -> Electron renderer 聚合窗口
  -> Electron main IPC
  -> inference-service.js
  -> yp_fault_infer.exe
  -> ONNX Runtime
  -> 推理结果
  -> 门控/投票后处理
  -> UI 显示和报警锁存
```

关键文件：

| 文件 | 说明 |
| --- | --- |
| `desktop/renderer/app.js` | 实时窗口聚合、推理调用、报警判断。 |
| `desktop/inference-service.js` | 启动 C++ 推理子进程并发送 JSON-RPC 请求。 |
| `desktop/inference/onnxruntime/src/main.cpp` | C++ 推理程序，包含预处理、后处理和门控。 |
| `desktop/models/sage_cnn/model_manifest.json` | 模型清单。 |
| `desktop/models/sage_cnn/scaler.json` | 归一化参数。 |
| `desktop/models/sage_cnn/realtime_sage_cnn_guard_config.json` | 实时门控配置。 |

### 10.2 模型输入

模型输入固定为：

```text
[1, 15, 50]
```

含义：

- batch = 1
- 通道数 = 15
- 时间窗口 = 50 点

桌面端每收到一次 `/odom`，就从缓存中取最新传感器值组成一行。

15 个特征顺序：

```text
odom_vx
odom_vy
odom_wz
wheel_speed0
wheel_speed1
wheel_speed2
imu_ax
imu_ay
imu_az
imu_gx
imu_gy
imu_gz
current0
current1
current2
```

窗口规则：

| 参数 | 当前值 | 说明 |
| --- | ---: | --- |
| `windowSize` | 50 | 满 50 行后开始推理。 |
| `stepSize` | 10 | 每新增 10 行触发一次推理。 |

`/wheel_speed` 是必需输入。如果没有三路轮速，桌面端显示等待 `/wheel_speed`，不会用 0 自动补齐。

### 10.3 当前模型包

当前默认模型目录：

```text
desktop/models/sage_cnn
```

应包含：

```text
model_manifest.json
sage_cnn_selected_best_model.onnx
scaler.json
feature_config_used.json
realtime_sage_cnn_guard_config.json
```

当前类别顺序：

```text
normal
wheel_slip
drive_abnormal
shaft_eccentricity
```

含义：

| 类别 | 中文说明 |
| --- | --- |
| `normal` | 正常。 |
| `wheel_slip` | 轮子打滑或轮面异常。 |
| `drive_abnormal` | 驱动异常。 |
| `shaft_eccentricity` | 电机轴偏心。 |

注意：类别顺序必须与模型训练时 logits 顺序一致。桌面端概率条、manifest 和导出脚本都应保持一致。

### 10.4 静止门控

静止门控用于避免小车静止时被误识别为故障。

配置文件：

```text
desktop/models/sage_cnn/realtime_sage_cnn_guard_config.json
```

关键参数：

| 参数 | 当前值 | 说明 |
| --- | ---: | --- |
| `static_linear_speed_threshold` | 0.08 | 平均线速度静止阈值。 |
| `static_angular_speed_threshold` | 0.08 | 平均角速度静止阈值。 |
| `static_wheel_speed_threshold` | 0.08 | 平均轮速静止阈值。 |
| `static_required_windows` | 5 | 连续 5 个静止窗口后确认静止。 |
| `static_display_label` | `normal_static` | 静止门控显示标签。 |
| `static_report_label` | `normal` | 静止门控内部归属正常类别。 |

当连续静止窗口满足条件时，推理程序会直接返回：

```text
class_name = normal_static
confidence = 1.0
backend = guard
device = static_gate
```

桌面端报警逻辑已经将 `normal_static` 归为正常，不会触发故障锁存。

### 10.5 置信度和投票稳定

非静止状态下，模型会正常推理，然后经过后处理：

- top1 置信度低于 `0.7` 时认为不稳定。
- top1 与 top2 差值低于 `0.15` 时认为不稳定。
- 最近 5 次预测中，某类达到 4 次才更新稳定类别。
- `wheel_slip` 与 `shaft_eccentricity` 如果置信度接近，会保持上一次稳定结果，避免来回跳变。

当前关键配置：

```text
vote_window_size = 5
vote_required_count = 4
low_confidence_threshold = 0.7
margin_threshold = 0.15
```

## 11. 故障报警逻辑

桌面端故障报警是 UI 层的安全提示和控制保护，不会发布 ROS 故障话题。

### 11.1 正常与故障判断

当前正常类别：

```text
normal
normal_static
```

其他类别均视为故障候选：

```text
wheel_slip
drive_abnormal
shaft_eccentricity
```

### 11.2 锁存条件

报警锁存必须满足：

```text
连续 3 次出现相同故障类别
```

示例 1：会锁存

```text
shaft_eccentricity -> 1/3
shaft_eccentricity -> 2/3
shaft_eccentricity -> 3/3 -> 锁存
```

示例 2：不会直接锁存，会重新计数

```text
wheel_slip         -> 1/3
drive_abnormal     -> 1/3
shaft_eccentricity -> 1/3
```

示例 3：正常状态会清空候选

```text
shaft_eccentricity -> 1/3
normal_static      -> 清空
shaft_eccentricity -> 1/3
```

### 11.3 锁存反馈

如果检测到轴偏心并连续出现 3 次：

```text
shaft_eccentricity
shaft_eccentricity
shaft_eccentricity
```

桌面端会：

- 报警状态显示为已锁存。
- 锁存故障显示 `shaft_eccentricity`。
- 报警置信度显示对应置信度。
- 连续计数显示 `3/3`。
- 首次触发显示该轮候选第一次出现时间。
- 最近触发显示最近一次故障出现时间。
- 状态栏 `RESET` 按钮启用并闪烁。
- 事件日志写入故障锁存记录。
- 如果正在巡航，自动停止巡航。
- 调用手动停车逻辑，停止桌面端控制输出。

### 11.4 首次触发与最近触发

两者不是同一个概念：

- 首次触发：这一轮同类故障候选第一次出现的时间。
- 最近触发：最近一次出现该故障的时间。

刚出现第一次故障时，两者相同。后续同一故障连续出现时，首次触发保持不变，最近触发持续更新。

### 11.5 不会自动执行的行为

当前故障报警不会：

- 发布 ROS 故障话题。
- 向下位机发送故障状态。
- 自动断开 rosbridge。
- 自动关闭桌面程序。
- 语音播报。

它主要完成桌面端显示、锁存提示和停止桌面端控制输出。

## 12. 数据采集

### 12.1 采集内容

数据采集用于构建故障诊断数据集。主要采集：

- 机器人位置。
- 机器人速度。
- IMU 加速度。
- IMU 角速度。
- 电池电压。
- 三路电流。
- 控制命令。
- 故障标签。
- 实验运行 ID。
- 运动模式。

### 12.2 故障标签

常用标签：

| 标签 | 名称 | 说明 |
| --- | --- | --- |
| 0 | `normal` | 正常。 |
| 1 | `drive_abnormal` 或 `drive_fault` | 驱动异常。 |
| 2 | `wheel_slip` | 轮子打滑。 |
| 3 | `shaft_eccentricity` 或 `shaft_eccentric` | 电机轴偏心。 |

注意：训练和推理时应统一类别名称和顺序。

### 12.3 采集命令

正常数据：

```bash
roslaunch turn_on_wheeltec_robot data_collector.launch fault_label:=0
```

驱动异常：

```bash
roslaunch turn_on_wheeltec_robot data_collector.launch fault_label:=1
```

轮子打滑：

```bash
roslaunch turn_on_wheeltec_robot data_collector.launch fault_label:=2
```

电机轴偏心：

```bash
roslaunch turn_on_wheeltec_robot data_collector.launch fault_label:=3
```

### 12.4 桌面端采集

桌面端可在数据采集页面配置：

- 输出目录。
- 电流传感器串口。
- 故障类别。
- 运动模式。
- run id。
- 采集频率期望值。

开始采集后，桌面端通过 ROS topic 控制采集节点，并通过 HTTP API 展示 CSV 文件列表、预览和统计。

## 13. 数据集构建

桌面端提供数据集构建入口，后端使用数据处理脚本完成：

- CSV 数据读取。
- 特征选择。
- 窗口切分。
- 归一化。
- 训练/验证/测试划分。
- 数据集结果保存。

当前故障诊断模型使用：

```text
15 通道
50 点窗口
10 点步长
standard scaler
```

训练时必须保证：

- 特征顺序与桌面端推理一致。
- 标签顺序与 `model_manifest.json` 一致。
- scaler 与 `scaler.json` 一致。
- 输入布局为 channel-time，即 `[1, 15, 50]`。

## 14. 模型导出与替换

### 14.1 导出要求

桌面端不能直接加载 PyTorch `.pth`。必须导出为 ONNX 模型包。

一个完整模型包至少包括：

```text
model_manifest.json
sage_cnn_selected_best_model.onnx
scaler.json
feature_config_used.json
```

建议同时包括：

```text
realtime_sage_cnn_guard_config.json
```

### 14.2 命令行导出

进入桌面端目录：

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop"
```

执行：

```powershell
.\python\Scripts\python.exe .\inference\tools\export_sage_cnn_onnx.py `
  --model-root "你的训练工程根目录" `
  --selected-dir "你的新模型目录" `
  --output-dir "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop\models\sage_cnn"
```

`selected-dir` 中应包含：

```text
sage_cnn_selected_best_model.pth
strict_scaler.pkl
feature_config_used.json
```

### 14.3 桌面端导入

在桌面端设置页中：

1. 填写模型代码目录。
2. 填写已选模型目录。
3. 填写导出目录。
4. 确认 Python 运行时。
5. 点击转换模型。
6. 转换成功后自动回填模型清单。
7. 点击 Reload 或等待自动加载。

状态显示 `ready` 后可以实时推理。

### 14.4 ONNX 单文件说明

当前导出脚本设置：

```text
external_data=False
```

因此模型导出为单个 `.onnx` 文件，不再依赖 `.onnx.data` 外部数据文件。若仓库中旧的 `.onnx.data` 被删除，这是预期行为，前提是当前 `.onnx` 能正常加载。

## 15. 桌面端打包

### 15.1 编译真实推理后端

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop"
npm run build:infer
```

首次运行会下载或定位 ONNX Runtime，并编译：

```text
yp_fault_infer.exe
```

### 15.2 离线占位推理

仅测试 UI 和打包流程：

```powershell
npm run build:infer:offline
```

该模式不能真实推理。

### 15.3 Windows 目录打包

```powershell
npm run build:win:dir
```

### 15.4 Windows 安装包

```powershell
npm run build:win
```

输出目录：

```text
desktop/dist
```

### 15.5 打包资源

`electron-builder.yml` 会带上：

- Electron 主程序。
- renderer 页面资源。
- SQLite 数据库代码。
- 推理程序。
- ONNX Runtime 动态库。
- `models/` 默认模型包。
- 图标和背景资源。

## 16. 最终演示流程建议

### 16.1 机器人侧

启动底盘：

```bash
roslaunch turn_on_wheeltec_robot turn_on_wheeltec_robot.launch
```

启动采集：

```bash
roslaunch turn_on_wheeltec_robot data_collector.launch fault_label:=0
```

启动 Web 控制和 API：

```bash
roslaunch turn_on_wheeltec_robot web_control.launch \
  start_base:=false \
  start_current_reader:=false \
  start_data_collector:=false
```

检查话题：

```bash
rostopic hz /odom
rostopic hz /wheel_speed
rostopic hz /current_data
rostopic hz /imu
```

### 16.2 桌面端

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop"
npm start
```

操作顺序：

1. 输入机器人 IP。
2. 点击连接。
3. 确认状态为在线。
4. 确认 `/odom`、电流、IMU、轮速有数据。
5. 确认故障诊断状态为 ready。
6. 打开 `FAULT ON`。
7. 让小车静止，观察 `normal_static` 不触发报警。
8. 运行正常运动，观察 `normal`。
9. 执行故障实验，观察故障类别和报警锁存。
10. 点击 RESET 清除锁存。

### 16.3 轴偏心故障演示

当模型连续 3 次识别到：

```text
shaft_eccentricity
```

预期表现：

- 识别结果显示 `shaft_eccentricity`。
- 报警面板连续计数从 `1/3` 到 `3/3`。
- 报警状态变为锁存。
- 锁存故障显示 `shaft_eccentricity`。
- 巡航停止。
- 手动控制输出停止。
- RESET 按钮可用。

## 17. 验证命令

### 17.1 JS 语法检查

在桌面端目录：

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop"
node --check .\renderer\app.js
node --check .\inference-service.js
node --check .\model-converter-service.js
```

如果当前目录是 ROS 包根目录：

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot"
node --check .\desktop\renderer\app.js
```

注意不要在 `desktop` 目录下再写 `.\desktop\renderer\app.js`，否则路径会变成：

```text
desktop\desktop\renderer\app.js
```

### 17.2 JSON 配置检查

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot"
node -e "const fs=require('fs'); for (const f of ['desktop/models/sage_cnn/model_manifest.json','desktop/models/sage_cnn/scaler.json','desktop/models/sage_cnn/feature_config_used.json','desktop/models/sage_cnn/realtime_sage_cnn_guard_config.json']) { JSON.parse(fs.readFileSync(f,'utf8')); console.log('OK', f); }"
```

### 17.3 模型文件检查

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot"
Get-ChildItem .\desktop\models\sage_cnn
```

应至少看到：

```text
model_manifest.json
sage_cnn_selected_best_model.onnx
scaler.json
feature_config_used.json
realtime_sage_cnn_guard_config.json
```

### 17.4 Git 差异检查

```powershell
git status --short
git diff --stat
git diff --check
```

`git diff --check` 无输出代表没有明显空白错误。

## 18. 常见问题

### 18.1 桌面端连接成功但没有速度

检查：

```bash
rostopic hz /odom
```

如果没有 `/odom`，说明底盘节点未启动或串口异常。

### 18.2 故障诊断一直准备中

检查：

```bash
rostopic hz /odom
rostopic hz /wheel_speed
rostopic hz /current_data
rostopic hz /imu
```

最常见原因是缺少 `/wheel_speed`。

### 18.3 桌面端显示等待 `/wheel_speed`

模型需要三路轮速。如果没有轮速，系统不会用 0 填充。

处理：

- 检查底盘节点是否发布 `/wheel_speed`。
- 检查 rosbridge 是否订阅到该话题。
- 检查话题类型是否为 `std_msgs/Float32MultiArray`。

### 18.4 `normal_static` 是否是故障

不是。

`normal_static` 是静止门控输出，表示机器人处于静止正常状态。桌面端已将其归为正常类别，不会触发报警锁存。

### 18.5 首次触发和最近触发为什么一样

第一次检测到故障时，两者相同。

同一故障连续出现后：

- 首次触发保持第一次时间。
- 最近触发更新为最近一次时间。

如果中间出现 `normal` 或 `normal_static`，候选会清空，下次故障重新计时。

### 18.6 不同故障连续出现会不会锁存

不会直接锁存。

当前逻辑要求连续 3 次相同故障类别才锁存。

### 18.7 ONNX Runtime backend unavailable

可能原因：

- 使用了 `build:infer:offline`。
- `yp_fault_infer.exe` 缺失。
- `onnxruntime.dll` 缺失。
- ONNX Runtime 下载或编译失败。

处理：

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop"
npm run build:infer
```

### 18.8 npm start 报 SQLite 原生模块错误

执行：

```powershell
cd "D:\projects\01 ROS\turn_on_wheeltec_robot\desktop"
npx electron-builder install-app-deps
```

### 18.9 node --check 路径错误

如果你当前目录是：

```text
D:\projects\01 ROS\turn_on_wheeltec_robot\desktop
```

使用：

```powershell
node --check .\renderer\app.js
```

如果你当前目录是：

```text
D:\projects\01 ROS\turn_on_wheeltec_robot
```

使用：

```powershell
node --check .\desktop\renderer\app.js
```

## 19. 最终版本注意事项

### 19.1 建议纳入最终代码包的内容

- `turn_on_wheeltec_robot/src`
- `turn_on_wheeltec_robot/include`
- `turn_on_wheeltec_robot/scripts`
- `turn_on_wheeltec_robot/launch`
- `turn_on_wheeltec_robot/config`
- `turn_on_wheeltec_robot/map`
- `turn_on_wheeltec_robot/web`
- `turn_on_wheeltec_robot/desktop`
- `turn_on_wheeltec_robot/docs`
- `turn_on_wheeltec_robot/README.md`
- `last readme.md`

### 19.2 可选择排除的本机配置

根目录中以下通常是本机开发环境配置，打包提交前可按需要排除：

```text
.idea/
.vscode/
.claude/
```

### 19.3 模型文件注意

当前模型包采用单文件 ONNX：

```text
sage_cnn_selected_best_model.onnx
```

不再依赖：

```text
sage_cnn_selected_best_model.onnx.data
```

如果后续重新导出模型，需要确认：

- ONNX 文件存在。
- manifest 指向正确。
- scaler 与训练一致。
- label 顺序与训练 logits 一致。
- 桌面端概率条顺序与 manifest 一致。

### 19.4 当前报警策略

最终版报警策略建议写入论文：

```text
系统将 normal 和 normal_static 视为正常状态。
对于 wheel_slip、drive_abnormal、shaft_eccentricity 等故障类别，只有连续 3 个推理窗口输出相同故障类别时，才触发报警锁存。
锁存后桌面端停止巡航和手动控制输出，并保持报警状态，直到用户手动 RESET。
```

### 19.5 当前静止误报抑制策略

最终版静止门控策略建议写入论文：

```text
系统在模型推理前统计窗口内线速度、角速度和三路轮速均值。
当连续多个窗口满足静止阈值时，跳过模型推理并输出 normal_static。
normal_static 在 UI 中显示为静止正常状态，在报警逻辑中归入 normal 类别，从而避免静止状态下传感器噪声导致故障误报。
```

## 20. 论文中可描述的系统创新点

可从以下角度总结：

1. 多源传感器融合：融合里程计、IMU、轮速和电流信号进行故障诊断。
2. 实时窗口推理：桌面端以 50 点滑动窗口构造模型输入，实现在线诊断。
3. 本机 ONNX 推理：采用独立 C++ 推理进程，降低 Electron 主界面负担。
4. 静止门控：针对静止状态误报问题加入运动门控机制。
5. 投票稳定：针对模型类别抖动加入置信度、margin 和滑动投票后处理。
6. 报警锁存：只有连续 3 次相同故障才锁存，提高报警可靠性。
7. 桌面端集成：将控制、监测、采集、实验、诊断和报警集成到统一界面。
8. 模型可替换：支持将新训练 `.pth` 模型导出为 ONNX 模型包并加载到桌面端。

## 21. 最小复现清单

如果后续需要在新机器上复现，按以下顺序：

1. 准备 ROS 和 catkin 工作空间。
2. 放入 `turn_on_wheeltec_robot` 包。
3. 安装 ROS 依赖和 `rosbridge_server`。
4. 执行 `catkin_make`。
5. 检查底盘串口和电流串口。
6. 启动底盘节点。
7. 启动 rosbridge 和 Web API。
8. 进入 `desktop` 执行 `npm install`。
9. 执行 `npm run build:infer`。
10. 执行 `npm start`。
11. 连接机器人 IP。
12. 检查 `/odom`、`/wheel_speed`、`/current_data`、`/imu`。
13. 检查故障诊断 ready。
14. 测试 `normal_static` 不报警。
15. 测试同类故障连续 3 次报警锁存。

## 22. 最终结论

本工程最终形成了一个较完整的机器人故障诊断实验平台。ROS 侧完成底盘控制、传感器数据发布、Web 控制安全适配和数据采集；桌面端完成实时监控、实验管理、数据预览、模型推理和报警锁存；推理后端完成 ONNX 模型加载、归一化、静止门控、置信度筛选、投票稳定和结果输出。

当前最终版重点行为如下：

- 桌面端可实时连接机器人 rosbridge。
- 推理输入为 15 通道、50 点窗口。
- 当前类别顺序为 `normal, wheel_slip, drive_abnormal, shaft_eccentricity`。
- `normal_static` 属于正常状态，不触发报警。
- 故障报警必须连续 3 次相同故障才锁存。
- 锁存后停止桌面端巡航和手动控制输出。
- 模型包为单文件 ONNX，不依赖 `.onnx.data`。
- 报警面板已调整为六行纵向状态列表，便于现场观察。

这份文档可作为最终代码包入口说明，也可作为毕业设计论文中“系统设计、软件实现、使用说明和实验平台搭建”的补充材料。

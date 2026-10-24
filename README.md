# 三全向轮机器人故障诊断毕业设计

杨鹏（Yang Peng）本科毕业设计工程，围绕 WHEELTEC R550PLUS 三全向轮机器人，保存电流传感器、底盘固件、ROS 控制与采集，以及多传感器故障诊断的代码、数据和实验结果。

本仓库原名 `yp---graduation-design`，整理后名为 **robot-fault-diagnosis-thesis**。它保留完整系统与实验上下文；持续维护的 ROS/Web/Electron 应用入口为 [wheeltec-robot-platform](https://github.com/y-gougou/wheeltec-robot-platform)。两者的 ROS 代码有版本差异，不能仅按目录相似直接覆盖。

## 四个子系统

| 实际目录 | 内容 | 入口 |
| --- | --- | --- |
| `01_ROS/turn_on_wheeltec_robot/` | ROS Noetic 底盘通信、采集、Web/Electron、故障推理的项目快照 | [ROS README](01_ROS/turn_on_wheeltec_robot/README.md) |
| `02 4CH-Current/` | STM32F103 电流采集固件、Python 上位机、独立 ROS 驱动、标定工具 | [HostApp](02%204CH-Current/HostApp/README.md)、[ROS 驱动](02%204CH-Current/ROS/ch4_current_sensor/README.md)、[标定](02%204CH-Current/Tools/README_Calibration.md) |
| `03 omi_car/` | STM32F4 全向轮底盘、FreeRTOS、电机 PID、IMU 与串口通信 | [底盘 README](03%20omi_car/README.md) |
| `04 last dance/last dance/` | 原始传感器 CSV、SAGE-CNN 系列训练、对比/消融实验、部署导出 | [训练与实验说明](04%20last%20dance/last%20dance/ypmodel/README_final_sage_cnn.md) |

系统链路为：底盘与电流板采样 → ROS 汇总并记录 CSV → 离线训练和实验 → 导出模型、scaler、特征配置 → 桌面端推理。

目录名称中的空格属于现有结构；命令行进入目录时请加引号。ROS 实际目录为 `01_ROS`，部分历史文档中的 `01 ROS` 路径需要据此调整。

## ROS 快照与维护版本

本仓库的 `01_ROS/turn_on_wheeltec_robot` 是完整毕业设计的一部分。机器人应用层的新维护入口为 [wheeltec-robot-platform](https://github.com/y-gougou/wheeltec-robot-platform)，该版本增加了当前串口帧 BCC 校验、电流配置处理、底盘循环限速、巡航心跳保护等修复，并将电流串口默认值改为 `/dev/ttyUSB1`。本仓库 ROS launch 仍默认 `/dev/ttyUSB0`。

两者 ROS 包名都为 `turn_on_wheeltec_robot`，同一 catkin 工作空间只能放一个。复现实验时使用对应历史快照；开展应用开发时以维护仓库 README 为入口，并记录所用固件、模型和数据版本。

构建本仓库 ROS 快照时，只将 `01_ROS/turn_on_wheeltec_robot` 放入已准备好的 ROS Noetic catkin 工作空间的 `src/`，然后执行：

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
roslaunch turn_on_wheeltec_robot web_control.launch \
  current_port:=/dev/ttyUSB0 \
  start_fdilink_ahrs:=false
```

外置 N100/FDI IMU、建图和导航功能需要相应驱动与依赖。Web 页面默认端口 8000，rosbridge 为 9090。此目录未包含 `meshes/`，部分 URDF 的可视化资源须从 [开发历史资产](https://github.com/y-gougou/wheeltec-development-history/tree/668af4ad85521e6a91191258c2b77c7dfeb5a3ca/turn_on_wheeltec_robot/meshes) 按需取得，勿将原始约 1.11 GB 的全部网格无差别复制进应用项目。

## 电流传感器与底盘固件

电流板工程位于 `02 4CH-Current/Firmware/`，使用 STM32F103C8T6/HAL；Keil 工程为 `Firmware/MDK-ARM/4CH-Current.uvprojx`。独立上位机要求 Python 3.10+，依赖以 `HostApp/pyproject.toml` 为准：

```bash
cd "02 4CH-Current/HostApp"
uv sync
uv run ch4-current
```

独立 ROS 驱动的包名是 `ch4_current_sensor`。将该子包放入 catkin 工作空间、安装声明依赖并编译后，其启动入口为：

```bash
roslaunch ch4_current_sensor sensor.launch port:=/dev/ttyUSB0 baudrate:=115200
```

**协议需要先统一：**当前固件 `uart_protocol.h` 中 `UART_PROTOCOL_TYPE=1`，选择 FireWater 文本协议，实际电流包为三个有效通道；独立 HostApp 的 `protocol.py` 与独立 ROS 驱动的 `sensor_node.py` 使用 `0xAA 0x55` 二进制帧解析。HostApp 旧 README 的“自动识别两种协议”描述与当前代码不一致。切换到二进制时仍须检查字段数量、长度和校验规则，不能只改开关就认定兼容。主 ROS 包自己的 current reader 则对应文本电流帧。

底盘工程位于 `03 omi_car/`，使用 STM32F4、FreeRTOS 和 Keil AC5/EIDE；入口为 `USER/main.c`，控制与状态位于 `BALANCE/`。编译和硬件设置见该子目录 README。底盘串口、角度控制、轮速及故障配置扩展需要与上位机协议匹配；本次仓库整理未进行编译、烧录或实车验证。

## 数据、训练与部署

原始数据位于 `04 last dance/last dance/shuju0517/`，包含正常、驱动异常、打滑、轴偏心四类目录，共 66 个 CSV。代码与已保存实验结果位于相邻的 `ypmodel/`；保留的结果包括主实验、跨速度泛化、部署鲁棒性、图表、模型权重和最终汇总。

训练使用 PyTorch、NumPy、scikit-learn 等依赖；绘图需要 matplotlib。工程未提供统一锁定的训练环境，复现时应记录 Python、PyTorch、设备与依赖版本，详见子项目说明。统一实验入口支持：

```bash
cd "04 last dance/last dance/ypmodel"

# 用独立输出目录进行短流程验证
python run_experiments.py --mode paper_main_vx05 --smoke \
  --output_dir results_smoke_paper_main_vx05 --require_figures

# 三阶段完整实验；使用新输出目录，保留仓库内现有结果
python run_experiments.py --mode paper_main_vx05 \
  --output_dir results_reproduction_main --require_figures
python run_experiments.py --mode paper_generalization \
  --main_results results_reproduction_main \
  --output_dir results_reproduction_generalization --require_figures
python run_experiments.py --mode deployment_robust \
  --output_dir results_reproduction_deployment --require_figures
```

统一入口默认数据位置为 `../shuju0517`，窗口大小 50、步长 10，输入排列为 `[batch, channel, time]`，模型输入通常为 `[1, 15, 50]`。15 个特征来自里程计 3、轮速 3、IMU 6、电流 3；必须保持训练时的特征顺序。

当前导出配置、统一训练入口和所选模型配置一致使用以下标签：

| 标签 | 类别 |
| --- | --- |
| 0 | normal |
| 1 | wheel_slip |
| 2 | drive_abnormal |
| 3 | shaft_eccentricity |

旧训练 README 前段及部分采集文档使用不同的 1/2 编号，复用 CSV 与模型前必须明确映射。部署以模型配套的 `label_map.json`、特征配置为准，不能仅按文件夹顺序或旧表格推断。

当前 `results_deployment_robust/export/inference_config.json` 标明导出模型为 **sage_no_saf，run 03**；`selected_sage_cnn_model/feature_config_used.json` 也记录这一选择。它是 SAGE-CNN 去 SAF 的部署变体，不能仅凭文件名 `sage_cnn_selected_best_model` 认为它是完整主模型。

保留并配套使用：

- `results_deployment_robust/export/`：ONNX/PT、特征列、标签映射、scaler 均值/标准差、推理配置。
- `selected_sage_cnn_model/`：所选权重、`strict_scaler.pkl`、特征配置。
- 各实验目录中的划分、指标、权重和图表，用于追溯结果。

ROS 桌面推理接口使用自己的 manifest/scaler 文件格式，接入时按 [维护平台推理文档](https://github.com/y-gougou/wheeltec-robot-platform/blob/master/docs/FAULT_INFERENCE.md) 完成配套转换与验证，不把单个 ONNX 文件当作完整部署包。

## 历史与相关仓库

| 入口 | 用途 |
| --- | --- |
| [wheeltec-robot-platform](https://github.com/y-gougou/wheeltec-robot-platform) | 维护中的 ROS/Web/Electron 平台，原 `0816` |
| [wheeltec-development-history](https://github.com/y-gougou/wheeltec-development-history) | 早期 ROS 开发链与原始 meshes，原 `0510` |
| [本仓库 archive/ros-package-0520 分支](https://github.com/y-gougou/robot-fault-diagnosis-thesis/tree/archive/ros-package-0520) | 保存早期 `ros-package--0520` 提交位置 |
| [archive-thesis-20260520](https://github.com/y-gougou/archive-thesis-20260520) | 原 `ros-package--0520` 独立历史入口 |

本次整理仅新增文档和关联入口，未删除代码、数据、模型、固件或历史提交。文档中的启动和实验命令已按现有文件核对，但尚未在对应机器人与训练环境执行验证。

作者：杨鹏（Yang Peng），燕山大学本科毕业设计。保留各子项目、WHEELTEC、STM32/HAL、FreeRTOS 及其他第三方组件原有的作者与许可证信息；本总览不替各组件重新指定许可证。

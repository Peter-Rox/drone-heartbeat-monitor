import streamlit as st
import time
import pandas as pd
import plotly.express as px
from datetime import datetime
import folium
from streamlit_folium import st_folium
# ------------------- 南科院航线地图固定参数 -------------------
# 南京科技职业学院地图中心点经纬度
SCHOOL_CENTER = [32.234111, 118.749428]

# 环绕校园闭环飞行航线（首尾坐标一致，航线自动闭合）
flight_route = [
    [32.2360, 118.7475],
    [32.2365, 118.7510],
    [32.2338, 118.7518],
    [32.2320, 118.7505],
    [32.2315, 118.7472],
    [32.2332, 118.7465],
    [32.2350, 118.7470],
    [32.2360, 118.7475]
]

# 飞行任务点：起飞、3个巡检拍照点、降落点
mission_list = [
    {"name": "起飞点", "pos": [32.2341, 118.7494], "color": "green", "task": "解锁起飞，飞行高度30米"},
    {"name": "巡检点位1", "pos": [32.2362, 118.7498], "color": "blue", "task": "全景广角拍照1张"},
    {"name": "巡检点位2", "pos": [32.2330, 118.7512], "color": "blue", "task": "倾斜摄影地形采集"},
    {"name": "巡检点位3", "pos": [32.2318, 118.7478], "color": "blue", "task": "定点持续录像10秒"},
    {"name": "降落点", "pos": [32.2341, 118.7494], "color": "red", "task": "自动返航垂直降落"}
]

# 避障禁飞区域（教学楼、高压电塔，红色半透明遮挡）
obstacle_area = [
    {
        "name": "一号教学楼禁飞区",
        "coords": [
            [32.2348, 118.7480],
            [32.2348, 118.7492],
            [32.2335, 118.7494],
            [32.2334, 118.7478]
        ]
    },
    {
        "name": "北区高压电塔禁飞区",
        "coords": [
            [32.2363, 118.7488],
            [32.2366, 118.7493],
            [32.2360, 118.7496],
            [32.2357, 118.7490]
        ]
    }
]
# 初始化会话状态
if "heartbeat_data" not in st.session_state:
    st.session_state["heartbeat_data"] = []
if "last_receive_time" not in st.session_state:
    st.session_state["last_receive_time"] = time.time()
if "sequence_num" not in st.session_state:
    st.session_state["sequence_num"] = 0
if "is_running" not in st.session_state:
    st.session_state["is_running"] = False

st.set_page_config(page_title="无人机心跳监测系统", layout="wide")
st.title("🛸 无人机通信“心跳”监测可视化")

# 控制按钮区
col1, col2 = st.columns(2)
with col1:
    start_btn = st.button("开始模拟", disabled=st.session_state["is_running"])
with col2:
    stop_btn = st.button("停止模拟", disabled=not st.session_state["is_running"])

if start_btn:
    st.session_state["is_running"] = True
if stop_btn:
    st.session_state["is_running"] = False

# 状态显示区
status_placeholder = st.empty()
chart_placeholder = st.empty()
log_placeholder = st.empty()

# 模拟心跳包发送与接收逻辑
if st.session_state["is_running"]:
    while st.session_state["is_running"]:
        # 模拟无人机每秒发送一个心跳包
        st.session_state["sequence_num"] += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        receive_timestamp = time.time()

        # 保存数据
        new_data = {
            "序号": st.session_state["sequence_num"],
            "时间": current_time,
            "时间戳": receive_timestamp
        }
        st.session_state["heartbeat_data"].append(new_data)
        st.session_state["last_receive_time"] = receive_timestamp

        # 检查是否掉线（超过3秒未收到则报警）
        time_since_last = time.time() - st.session_state["last_receive_time"]
        if time_since_last > 3:
            status_placeholder.error("⚠️ 无人机连接超时！已掉线！")
        else:
            status_placeholder.success("✅ 无人机连接正常，心跳接收中...")

        # 更新折线图
        df = pd.DataFrame(st.session_state["heartbeat_data"])
        fig = px.line(
            df,
            x="时间",
            y="序号",
            title="心跳包序号随时间变化曲线",
            markers=True
        )
        chart_placeholder.plotly_chart(fig, use_container_width=True)

        # 显示日志
        log_placeholder.dataframe(df[["序号", "时间"]].tail(10), use_container_width=True)

        # 等待1秒
        time.sleep(1)
else:
    # 停止时显示已有数据
    if st.session_state["heartbeat_data"]:
        df = pd.DataFrame(st.session_state["heartbeat_data"])
        fig = px.line(
            df,
            x="时间",
            y="序号",
            title="心跳包序号随时间变化曲线",
            markers=True
        )
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        log_placeholder.dataframe(df[["序号", "时间"]], use_container_width=True)
    else:
        status_placeholder.info("点击「开始模拟」启动无人机心跳监测")
# ===================== 无人机航线地图展示模块 =====================
st.divider()  # 分割线，和上方模拟功能隔开
st.subheader("🗺️ 南京科技职业学院 无人机航线规划地图")
st.info("图例说明：蓝色线条=巡检航线 | 绿/蓝/红标=任务点 | 红色半透明色块=建筑/高压塔避障区")

# 初始化地图画布
map_main = folium.Map(
    location=SCHOOL_CENTER,
    zoom_start=16,
    tiles="OpenStreetMap"
)

# 1. 绘制环绕校园闭环航线
folium.PolyLine(
    locations=flight_route,
    color="#0066ff",
    weight=4,
    opacity=0.8,
    tooltip="校园闭环巡检航线"
).add_to(map_main)

# 2. 批量绘制所有任务航点标记
for wp in mission_list:
    folium.Marker(
        location=wp["pos"],
        popup=f"点位名称：{wp['name']}\n执行任务：{wp['task']}",
        tooltip=wp["name"],
        icon=folium.Icon(color=wp["color"], icon="plane", prefix="fa")
    ).add_to(map_main)

# 3. 绘制红色避障禁飞区域
for obs in obstacle_area:
    folium.Polygon(
        locations=obs["coords"],
        color="#ff2222",
        fill=True,
        fill_color="#ff4444",
        fill_opacity=0.35,
        tooltip=f"避障区域：{obs['name']}"
    ).add_to(map_main)

# 将地图渲染到Streamlit网页页面
st_folium(map_main, width=1000, height=600)

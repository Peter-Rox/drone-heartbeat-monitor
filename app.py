import streamlit as st
import time
import pandas as pd
import plotly.express as px
from datetime import datetime

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

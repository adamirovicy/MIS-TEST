# -*- coding: utf-8 -*-
"""
个人信息管理程序 - Web 版
功能: 增、删、改、查、搜索个人信息
技术栈: Python + Streamlit + SQLite(本地) / MySQL(阿里云RDS)
部署: 阿里云 ECS / 函数计算 / SAE
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

# ---------- 数据库配置 ----------
# 优先从环境变量读取，否则使用本地 SQLite
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite 或 mysql

if DB_TYPE == "mysql":
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "persons_db"),
        "port": int(os.getenv("DB_PORT", "3306")),
    }
else:
    DB_PATH = os.getenv("DB_PATH", "persons.db")


def get_connection():
    """获取数据库连接"""
    if DB_TYPE == "mysql":
        import pymysql
        return pymysql.connect(**DB_CONFIG)
    else:
        return sqlite3.connect(DB_PATH)


def init_db():
    """初始化数据库，创建表"""
    conn = get_connection()
    cur = conn.cursor()

    if DB_TYPE == "mysql":
        cur.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                gender VARCHAR(10),
                birthday VARCHAR(20),
                phone VARCHAR(20),
                email VARCHAR(100),
                address VARCHAR(255),
                remark TEXT,
                created_at VARCHAR(30)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT,
                birthday TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                remark TEXT,
                created_at TEXT
            )
        """)

    conn.commit()
    conn.close()


def db_insert(person):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if DB_TYPE == "mysql":
        sql = """
            INSERT INTO persons (name, gender, birthday, phone, email, address, remark, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
    else:
        sql = """
            INSERT INTO persons (name, gender, birthday, phone, email, address, remark, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

    cur.execute(sql, (
        person["name"], person["gender"], person["birthday"],
        person["phone"], person["email"], person["address"],
        person["remark"], now
    ))
    conn.commit()
    conn.close()


def db_update(pid, person):
    conn = get_connection()
    cur = conn.cursor()

    if DB_TYPE == "mysql":
        sql = """
            UPDATE persons SET
                name=%s, gender=%s, birthday=%s, phone=%s, email=%s, address=%s, remark=%s
            WHERE id=%s
        """
    else:
        sql = """
            UPDATE persons SET
                name=?, gender=?, birthday=?, phone=?, email=?, address=?, remark=?
            WHERE id=?
        """

    cur.execute(sql, (
        person["name"], person["gender"], person["birthday"],
        person["phone"], person["email"], person["address"],
        person["remark"], pid
    ))
    conn.commit()
    conn.close()


def db_delete(pid):
    conn = get_connection()
    cur = conn.cursor()

    if DB_TYPE == "mysql":
        cur.execute("DELETE FROM persons WHERE id=%s", (pid,))
    else:
        cur.execute("DELETE FROM persons WHERE id=?", (pid,))

    conn.commit()
    conn.close()


def db_query(keyword=""):
    conn = get_connection()

    if DB_TYPE == "mysql":
        sql = """
            SELECT id, name, gender, birthday, phone, email, address, remark, created_at
            FROM persons
            WHERE name LIKE %s OR phone LIKE %s OR email LIKE %s OR remark LIKE %s
            ORDER BY id DESC
        """ if keyword else """
            SELECT id, name, gender, birthday, phone, email, address, remark, created_at
            FROM persons ORDER BY id DESC
        """
    else:
        sql = """
            SELECT id, name, gender, birthday, phone, email, address, remark, created_at
            FROM persons
            WHERE name LIKE ? OR phone LIKE ? OR email LIKE ? OR remark LIKE ?
            ORDER BY id DESC
        """ if keyword else """
            SELECT id, name, gender, birthday, phone, email, address, remark, created_at
            FROM persons ORDER BY id DESC
        """

    if keyword:
        like = f"%{keyword}%"
        df = pd.read_sql(sql, conn, params=(like, like, like, like))
    else:
        df = pd.read_sql(sql, conn)

    conn.close()
    return df


# ---------- Streamlit 页面配置 ----------
st.set_page_config(
    page_title="个人信息管理",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化数据库
init_db()

# ---------- 页面样式 ----------
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ---------- 侧边栏 ----------
with st.sidebar:
    st.markdown('<p class="main-header">📋 个人信息管理</p>', unsafe_allow_html=True)
    st.markdown("---")

    # 搜索
    search_keyword = st.text_input("🔍 搜索", placeholder="输入姓名、手机号、邮箱或备注关键词")

    st.markdown("---")
    st.markdown(f"**数据库类型:** `{DB_TYPE}`")
    if DB_TYPE == "mysql":
        st.markdown(f"**数据库地址:** `{DB_CONFIG['host']}`")
    st.markdown("---")
    st.markdown("### 使用说明")
    st.markdown("""
    1. 在右侧表单填写信息
    2. 点击 **新增** 保存记录
    3. 在列表中选择记录可编辑
    4. 点击 **删除** 移除记录
    """)

# ---------- 主页面 ----------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 信息编辑")

    # 表单
    name = st.text_input("姓名 *", placeholder="必填")
    gender = st.selectbox("性别", ["男", "女", "其他"], index=0)
    birthday = st.text_input("生日", placeholder="YYYY-MM-DD")
    phone = st.text_input("手机号")
    email = st.text_input("邮箱")
    address = st.text_area("地址", height=68)
    remark = st.text_area("备注", height=68)

    # 操作按钮
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    with btn_col1:
        if st.button("➕ 新增", type="primary", use_container_width=True):
            if not name.strip():
                st.warning("姓名不能为空")
            else:
                # 验证生日格式
                if birthday:
                    try:
                        datetime.strptime(birthday, "%Y-%m-%d")
                    except ValueError:
                        st.warning("生日格式应为 YYYY-MM-DD")
                        st.stop()

                db_insert({
                    "name": name.strip(),
                    "gender": gender,
                    "birthday": birthday.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "address": address.strip(),
                    "remark": remark.strip(),
                })
                st.success("新增成功！")
                st.rerun()

    with btn_col2:
        if st.button("🗑️ 删除", use_container_width=True):
            if "selected_id" in st.session_state and st.session_state.selected_id:
                db_delete(st.session_state.selected_id)
                st.success(f"已删除 ID={st.session_state.selected_id}")
                del st.session_state.selected_id
                st.rerun()
            else:
                st.info("请先从下方列表选择一条记录")

    with btn_col3:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

with col2:
    st.subheader("📊 人员列表")

    # 查询数据
    df = db_query(search_keyword)

    if df.empty:
        st.info("没有数据可以操作。")
    else:
        st.markdown(f"**共 {len(df)} 条记录**")

        # 显示数据表格
        display_df = df.copy()
        display_df.columns = ["ID", "姓名", "性别", "生日", "手机号", "邮箱", "地址", "备注", "创建时间"]

        # 使用 data_editor 或 dataframe + 选择
        event = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # 处理行选择
        if event.selection.rows:
            selected_idx = event.selection.rows[0]
            selected_row = df.iloc[selected_idx]
            st.session_state.selected_id = int(selected_row["id"])
            st.session_state.selected_data = selected_row.to_dict()

            # 显示选中详情
            with st.expander("📌 选中记录详情", expanded=True):
                st.json(st.session_state.selected_data)

                # 编辑表单
                st.markdown("### ✏️ 编辑此记录")
                edit_name = st.text_input("姓名", value=selected_row["name"], key="edit_name")
                edit_gender = st.selectbox("性别", ["男", "女", "其他"],
                                          index=["男", "女", "其他"].index(selected_row["gender"]) if selected_row["gender"] in ["男", "女", "其他"] else 0,
                                          key="edit_gender")
                edit_birthday = st.text_input("生日", value=selected_row["birthday"] or "", key="edit_birthday")
                edit_phone = st.text_input("手机号", value=selected_row["phone"] or "", key="edit_phone")
                edit_email = st.text_input("邮箱", value=selected_row["email"] or "", key="edit_email")
                edit_address = st.text_area("地址", value=selected_row["address"] or "", key="edit_address")
                edit_remark = st.text_area("备注", value=selected_row["remark"] or "", key="edit_remark")

                if st.button("💾 保存修改", type="primary"):
                    if not edit_name.strip():
                        st.warning("姓名不能为空")
                    else:
                        if edit_birthday:
                            try:
                                datetime.strptime(edit_birthday, "%Y-%m-%d")
                            except ValueError:
                                st.warning("生日格式应为 YYYY-MM-DD")
                                st.stop()

                        db_update(st.session_state.selected_id, {
                            "name": edit_name.strip(),
                            "gender": edit_gender,
                            "birthday": edit_birthday.strip(),
                            "phone": edit_phone.strip(),
                            "email": edit_email.strip(),
                            "address": edit_address.strip(),
                            "remark": edit_remark.strip(),
                        })
                        st.success("更新成功！")
                        st.rerun()

# ---------- 底部 ----------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "个人信息管理系统 | 技术支持: Streamlit + SQLite/MySQL"
    "</div>",
    unsafe_allow_html=True
)

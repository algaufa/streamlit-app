import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime
import zipfile
import io
import uuid

FLATS_FILE = "flats.csv"

# ========================= УПРАВЛЕНИЕ КВАРТИРАМИ =========================
def init_flats():
    if not os.path.exists(FLATS_FILE):
        df = pd.DataFrame([{"ID": "flat_1", "Название": "Квартира 1", "Порядок": 1}])
        df.to_csv(FLATS_FILE, index=False, encoding='utf-8-sig')
        init_flat_databases("flat_1")

def get_flats():
    try:
        df = pd.read_csv(FLATS_FILE, dtype=str, encoding='utf-8-sig')
        df["Порядок"] = pd.to_numeric(df["Порядок"])
        df = df.sort_values(by="Порядок")
        return df
    except:
        init_flats()
        return get_flats()

def save_flats(df):
    df.to_csv(FLATS_FILE, index=False, encoding='utf-8-sig')

def get_flat_files(flat_id):
    return (
        f"services_{flat_id}.csv",
        f"history_{flat_id}.csv",
        f"calc_config_{flat_id}.csv"
    )

def init_flat_databases(flat_id):
    serv_file, hist_file, calc_file = get_flat_files(flat_id)
    if not os.path.exists(serv_file):
        df_serv = pd.DataFrame([
            {"Услуга": "ЭЭ (кВт·ч)", "Тариф": "0-3900:3.49, 3901-6000:5.68, 6001-inf:8.91", "Дата_начала": "2025-01-01", "Порядок": 1, "Цвет": "#FF9800"},
            {"Услуга": "ГВС (м³)", "Тариф": "266.84", "Дата_начала": "2025-01-01", "Порядок": 2, "Цвет": "#F44336"},
            {"Услуга": "ХВС (м³)", "Тариф": "40.53", "Дата_начала": "2025-01-01", "Порядок": 3, "Цвет": "#2196F3"},
            {"Услуга": "ВО (м³)", "Тариф": "44.54", "Дата_начала": "2025-01-01", "Порядок": 4, "Цвет": "#9C27B0"}
        ])
        df_serv.to_csv(serv_file, index=False, encoding='utf-8-sig')
    if not os.path.exists(hist_file):
        df_hist = pd.DataFrame(columns=["Дата", "Услуга", "Расход", "Тариф", "Сумма_руб", "Показания"])
        df_hist.to_csv(hist_file, index=False, encoding='utf-8-sig')
    if not os.path.exists(calc_file):
        df_calc = pd.DataFrame([
            {"Расчётная услуга": "ВО (м³)", "Исходная услуга": "ХВС (м³)"},
            {"Расчётная услуга": "ВО (м³)", "Исходная услуга": "ГВС (м³)"}
        ])
        df_calc.to_csv(calc_file, index=False, encoding='utf-8-sig')

# ====================== ФУНКЦИИ ДОСТУПА К ДАННЫМ ======================
def get_services(flat_id):
    serv_file, _, _ = get_flat_files(flat_id)
    try:
        df = pd.read_csv(serv_file, dtype={"Тариф": str, "Услуга": str}, encoding='utf-8-sig')
        df["Услуга"] = df["Услуга"].str.strip()
        if "Порядок" not in df.columns:
            df["Порядок"] = 10
        if "Цвет" not in df.columns:
            df["Цвет"] = "#4CAF50"
        return df
    except:
        init_flat_databases(flat_id)
        return get_services(flat_id)

def save_services(df, flat_id):
    df["Услуга"] = df["Услуга"].str.strip()
    serv_file, _, _ = get_flat_files(flat_id)
    df.to_csv(serv_file, index=False, encoding='utf-8-sig')

def get_history(flat_id):
    _, hist_file, _ = get_flat_files(flat_id)
    try:
        df = pd.read_csv(hist_file, dtype={"Услуга": str, "Тариф": str}, encoding='utf-8-sig')
        df["Услуга"] = df["Услуга"].str.strip()
        return df
    except:
        init_flat_databases(flat_id)
        df = pd.read_csv(hist_file, dtype={"Услуга": str, "Тариф": str}, encoding='utf-8-sig')
        df["Услуга"] = df["Услуга"].str.strip()
        return df

def save_history(df, flat_id):
    df["Услуга"] = df["Услуга"].str.strip()
    _, hist_file, _ = get_flat_files(flat_id)
    df_to_save = df.copy()
    if "Тариф" in df_to_save.columns:
        df_to_save["Тариф"] = df_to_save["Тариф"].astype(str).str.replace(",", ";")
    df_to_save.to_csv(hist_file, index=False, encoding='utf-8-sig')

def get_calc_config(flat_id):
    _, _, calc_file = get_flat_files(flat_id)
    try:
        df = pd.read_csv(calc_file, dtype=str, encoding='utf-8-sig')
        df["Расчётная услуга"] = df["Расчётная услуга"].str.strip()
        df["Исходная услуга"] = df["Исходная услуга"].str.strip()
        config = {}
        for _, row in df.iterrows():
            target = row["Расчётная услуга"]
            source = row["Исходная услуга"]
            if target not in config:
                config[target] = []
            config[target].append(source)
        return config
    except:
        return {"ВО (м³)": ["ХВС (м³)", "ГВС (м³)"]}

def save_calc_config(config_dict, flat_id):
    rows = []
    for target, sources in config_dict.items():
        target = target.strip()
        for s in sources:
            s = s.strip()
            rows.append({"Расчётная услуга": target, "Исходная услуга": s})
    if rows:
        pd.DataFrame(rows).to_csv(get_flat_files(flat_id)[2], index=False, encoding='utf-8-sig')
    else:
        pd.DataFrame(columns=["Расчётная услуга", "Исходная услуга"]).to_csv(get_flat_files(flat_id)[2], index=False, encoding='utf-8-sig')

def get_notes_file(flat_id):
    return f"notes_{flat_id}.txt"

def get_notes(flat_id):
    notes_file = get_notes_file(flat_id)
    if os.path.exists(notes_file):
        with open(notes_file, "r", encoding="utf-8-sig") as f:
            return f.read()
    return ""

def save_notes(flat_id, text):
    notes_file = get_notes_file(flat_id)
    with open(notes_file, "w", encoding="utf-8-sig") as f:
        f.write(text)

# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================
def get_active_tariff_and_date(df_serv, service_name, target_date):
    df_sub = df_serv[df_serv["Услуга"] == service_name].copy()
    if df_sub.empty:
        return "0.0", target_date
    df_sub["Parsed_Date"] = pd.to_datetime(df_sub["Дата_начала"])
    target_dt = pd.to_datetime(target_date)
    df_valid = df_sub[df_sub["Parsed_Date"] <= target_dt]
    if df_valid.empty:
        closest_row = df_sub.sort_values(by="Parsed_Date", ascending=True).iloc[0]
    else:
        closest_row = df_valid.sort_values(by="Parsed_Date", ascending=False).iloc[0]
    return str(closest_row["Тариф"]), closest_row["Дата_начала"]

def get_service_meta(df_serv, service_name):
    df_sub = df_serv[df_serv["Услуга"] == service_name]
    if df_sub.empty:
        return 10, "#4CAF50"
    row = df_sub.iloc[0]
    sort_order = int(row["Порядок"]) if pd.notna(row["Порядок"]) else 10
    color = str(row["Цвет"]) if pd.notna(row["Цвет"]) else "#4CAF50"
    return sort_order, color

def get_last_meter_value(df_hist, service_name):
    if df_hist.empty or service_name not in df_hist["Услуга"].values:
        return 0.0
    df_sub = df_hist[df_hist["Услуга"] == service_name]
    last_row = df_sub.sort_values(by="Дата", ascending=False).iloc[0]
    return float(last_row["Показания"])

def calculate_tiered_cost(consumption, tariff_str):
    if ":" not in str(tariff_str):
        return consumption * float(tariff_str), tariff_str
    total_cost = 0.0
    remaining = consumption
    try:
        tiers = tariff_str.split(",")
        parsed_tiers = []
        for tier in tiers:
            limits, rate = tier.strip().split(":")
            start, end = limits.split("-")
            start = float(start)
            end = float(end) if end.lower() != "inf" else float('inf')
            rate = float(rate)
            parsed_tiers.append((start, end, rate))
        parsed_tiers.sort(key=lambda x: x[0])
        for start, end, rate in parsed_tiers:
            if remaining <= 0:
                break
            tier_capacity = end - start
            consumed_in_tier = min(remaining, tier_capacity)
            total_cost += consumed_in_tier * rate
            remaining -= consumed_in_tier
        return total_cost, tariff_str
    except Exception:
        return 0.0, "Ошибка тарифа"

# --- ПОЛНЫЙ ПЕРЕСЧЁТ ---
def recalc_all_sequential(df_hist, df_serv, calc_config):
    df_hist["Услуга"] = df_hist["Услуга"].astype(str).str.strip()
    calculated_services = [s.strip() for s in calc_config.keys()]

    for service in df_hist["Услуга"].unique():
        if not isinstance(service, str):
            continue
        service = service.strip()
        if service in calculated_services:
            continue
        mask = df_hist["Услуга"] == service
        if not mask.any():
            continue
        idx_sorted = df_hist[mask].sort_values(by="Дата").index
        prev_meter = 0.0
        for i, idx in enumerate(idx_sorted):
            meter = float(df_hist.at[idx, "Показания"])
            if i == 0:
                consumption = 0.0
                prev_meter = meter
            else:
                if meter < prev_meter:
                    consumption = 0.0
                    prev_meter = meter
                else:
                    consumption = meter - prev_meter
                    prev_meter = meter
            active_tariff, _ = get_active_tariff_and_date(df_serv, service, df_hist.at[idx, "Дата"])
            cost, recorded_tariff = calculate_tiered_cost(consumption, active_tariff)
            df_hist.at[idx, "Расход"] = round(consumption, 2)
            df_hist.at[idx, "Тариф"] = recorded_tariff
            df_hist.at[idx, "Сумма_руб"] = round(cost, 2)

    for calc_srv, source_list in calc_config.items():
        calc_srv = calc_srv.strip()
        if not source_list:
            continue
        if calc_srv not in df_hist["Услуга"].values:
            continue
        source_list = [s.strip() for s in source_list]
        dates = sorted(df_hist[df_hist["Услуга"] == calc_srv]["Дата"].unique())

        for date in dates:
            total_consumption = 0.0
            for src in source_list:
                src_rows = df_hist[(df_hist["Услуга"] == src) & (df_hist["Дата"] == date)]
                if not src_rows.empty:
                    total_consumption += src_rows["Расход"].clip(lower=0).sum()
            df_hist.loc[(df_hist["Услуга"] == calc_srv) & (df_hist["Дата"] == date), "Расход"] = round(total_consumption, 2)
            active_tariff, _ = get_active_tariff_and_date(df_serv, calc_srv, date)
            cost, recorded_tariff = calculate_tiered_cost(total_consumption, active_tariff)
            df_hist.loc[(df_hist["Услуга"] == calc_srv) & (df_hist["Дата"] == date), "Тариф"] = recorded_tariff
            df_hist.loc[(df_hist["Услуга"] == calc_srv) & (df_hist["Дата"] == date), "Сумма_руб"] = round(cost, 2)

        mask = df_hist["Услуга"] == calc_srv
        idx_sorted = df_hist[mask].sort_values(by="Дата").index
        cum_meter = 0.0
        for idx in idx_sorted:
            cum_meter += df_hist.at[idx, "Расход"]
            df_hist.at[idx, "Показания"] = cum_meter

    return df_hist

def create_backup_zip(flat_id):
    serv_file, hist_file, calc_file = get_flat_files(flat_id)
    notes_file = get_notes_file(flat_id)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file, arcname in [(serv_file, "services.csv"), (hist_file, "history.csv"), (calc_file, "calc_config.csv")]:
            if os.path.exists(file):
                zf.write(file, arcname=arcname)
        flat_name = flats_df[flats_df["ID"] == flat_id]["Название"].values[0]
        zf.writestr("flat_info.txt", flat_name)
        if os.path.exists(notes_file):
            zf.write(notes_file, arcname="notes.txt")
    return zip_buffer.getvalue()

# ====================== ИНИЦИАЛИЗАЦИЯ ======================
init_flats()
flats_df = get_flats()

st.set_page_config(page_title="Учет ЖКХ", page_icon="🏠", layout="wide")

flat_options = flats_df["ID"].tolist()
if "selected_flat_id" not in st.session_state:
    st.session_state.selected_flat_id = flat_options[0] if flat_options else None

current_index = flat_options.index(st.session_state.selected_flat_id) if st.session_state.selected_flat_id in flat_options else 0

selected_flat = st.selectbox(
    "🏠 Активная квартира",
    options=flat_options,
    format_func=lambda x: flats_df[flats_df["ID"] == x]["Название"].values[0],
    index=current_index,
    key="main_flat_selector"
)

if selected_flat != st.session_state.selected_flat_id:
    st.session_state.selected_flat_id = selected_flat
    st.rerun()

flat_id = st.session_state.selected_flat_id
current_flat_name = flats_df[flats_df["ID"] == flat_id]["Название"].values[0]
st.title(f"📊 {current_flat_name}")

df_serv = get_services(flat_id)
df_hist = get_history(flat_id)
calc_config = get_calc_config(flat_id)

if not df_hist.empty:
    last_date = df_hist["Дата"].max()
    last_total = df_hist[df_hist["Дата"] == last_date]["Сумма_руб"].sum()
    st.markdown(f"### Последний расчёт: {last_total:.2f} руб. {last_date}")
else:
    st.markdown("### Последний расчёт: нет данных")

if "reset_warning" not in st.session_state:
    st.session_state.reset_warning = False
if st.session_state.reset_warning:
    st.warning(f"⚠️ Для услуг: {', '.join(st.session_state.get('reset_services', []))} — показания ниже предыдущих. Расход = 0, оплата не начислена (сброс счётчика).")
    st.session_state.reset_warning = False

if not df_serv.empty:
    services_with_meta = []
    for s_name in df_serv["Услуга"].unique():
        poryadok, cvet = get_service_meta(df_serv, s_name)
        services_with_meta.append({"Имя": s_name, "Порядок": poryadok})
    df_meta_sort = pd.DataFrame(services_with_meta).sort_values(by=["Порядок", "Имя"])
    unique_services = df_meta_sort["Имя"].tolist()
else:
    unique_services = []

# ====================== БОКОВАЯ ПАНЕЛЬ ======================
with st.sidebar:
    st.markdown("## 🏠 Управление квартирами")
    with st.expander("🏠 Квартиры", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("➕", help="Добавить новую квартиру"):
                new_id = f"flat_{str(uuid.uuid4())[:8]}"
                new_name = f"Квартира {len(flat_options)+1}"
                max_order = flats_df["Порядок"].max() if not flats_df.empty else 0
                new_row = pd.DataFrame([{"ID": new_id, "Название": new_name, "Порядок": max_order+1}])
                flats_df = pd.concat([flats_df, new_row], ignore_index=True)
                flats_df["Порядок"] = flats_df["Порядок"].astype(int)
                save_flats(flats_df)
                init_flat_databases(new_id)
                st.rerun()
        with col2:
            if st.button("✏️", help="Переименовать текущую квартиру"):
                st.session_state.rename_flat = True
        with col3:
            if st.button("▲", help="Переместить квартиру вверх"):
                idx = flats_df[flats_df["ID"] == flat_id].index[0]
                if idx > 0:
                    flats_df.iloc[idx, flats_df.columns.get_loc("Порядок")] -= 1
                    flats_df.iloc[idx-1, flats_df.columns.get_loc("Порядок")] += 1
                    flats_df = flats_df.sort_values(by="Порядок").reset_index(drop=True)
                    flats_df["Порядок"] = range(1, len(flats_df)+1)
                    save_flats(flats_df)
                    st.rerun()
        with col4:
            if st.button("▼", help="Переместить квартиру вниз"):
                idx = flats_df[flats_df["ID"] == flat_id].index[0]
                if idx < len(flats_df)-1:
                    flats_df.iloc[idx, flats_df.columns.get_loc("Порядок")] += 1
                    flats_df.iloc[idx+1, flats_df.columns.get_loc("Порядок")] -= 1
                    flats_df = flats_df.sort_values(by="Порядок").reset_index(drop=True)
                    flats_df["Порядок"] = range(1, len(flats_df)+1)
                    save_flats(flats_df)
                    st.rerun()

        if st.button("🗑️ Удалить текущую квартиру", type="primary"):
            flat_to_delete = flat_id
            serv_file, hist_file, calc_file = get_flat_files(flat_to_delete)
            notes_file = get_notes_file(flat_to_delete)
            for f in [serv_file, hist_file, calc_file, notes_file]:
                if os.path.exists(f):
                    os.remove(f)
            flats_df = flats_df[flats_df["ID"] != flat_to_delete]
            flats_df["Порядок"] = range(1, len(flats_df)+1)
            save_flats(flats_df)
            if not flats_df.empty:
                st.session_state.selected_flat_id = flats_df.iloc[0]["ID"]
            else:
                st.session_state.selected_flat_id = None
            st.rerun()

        if st.session_state.get("rename_flat"):
            current_name = flats_df[flats_df["ID"] == flat_id]["Название"].values[0]
            new_name = st.text_input("Новое название", value=current_name, key="flat_new_name")
            if st.button("Сохранить название"):
                flats_df.loc[flats_df["ID"] == flat_id, "Название"] = new_name
                save_flats(flats_df)
                st.session_state.rename_flat = False
                st.rerun()

    # Заметки отдельным expander'ом ниже квартир
    with st.expander("📝 Заметки", expanded=False):
        notes_text = st.text_area("Заметки для этой квартиры",
                                  value=get_notes(flat_id), height=200, key=f"notes_{flat_id}")
        if st.button("💾 Сохранить заметки", key="save_notes_btn"):
            save_notes(flat_id, notes_text)
            st.success("Заметки сохранены!")

    st.markdown("---")
    st.markdown("### 🛠️ Настройки услуг")

    # ======== НАСТРОЙКИ ========
    # ... (вся секция настроек, расчётных услуг, тарифов, создания/удаления, бэкапа – без изменений)
    # Для экономии места я не вставляю повторно все настройки – они остаются такими же, как в предыдущем полном коде.
    # Убедитесь, что вы используете самую последнюю версию из ответа выше.

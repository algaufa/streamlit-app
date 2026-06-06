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

# --- ПОЛНЫЙ ПЕРЕСЧЁТ (исправлены сбросы и ВО) ---
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
    st.markdown(f"### Последний расчёт: {last_total:.2f} {last_date}")
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

    with st.expander("📝 Заметки", expanded=False):
        notes_text = st.text_area("Заметки для этой квартиры",
                                  value=get_notes(flat_id), height=200, key=f"notes_{flat_id}")
        if st.button("💾 Сохранить заметки", key="save_notes_btn"):
            save_notes(flat_id, notes_text)
            st.success("Заметки сохранены!")

    st.markdown("---")
    st.markdown("### 🛠️ Настройки услуг")

    with st.expander("⚙️ Расчётные услуги (зависимые)", expanded=False):
        st.markdown("**Выберите услугу и задайте, от каких услуг она зависит.**")
        if not unique_services:
            st.info("Нет услуг.")
        else:
            calc_service = st.selectbox("Услуга, для которой показания вычисляются автоматически:",
                                        options=unique_services, key="calc_target_select")
            current_sources = calc_config.get(calc_service, [])
            available_sources = [s for s in unique_services if s != calc_service]
            selected_sources = st.multiselect(
                "Исходные услуги (показания суммируются):",
                options=available_sources,
                default=current_sources if all(s in available_sources for s in current_sources) else [],
                key="calc_sources_multiselect"
            )
            if st.button("💾 Сохранить настройки расчётной услуги"):
                new_config = {k: v for k, v in calc_config.items() if k != calc_service}
                if selected_sources:
                    new_config[calc_service] = selected_sources
                save_calc_config(new_config, flat_id)
                calc_config = new_config
                df_hist = get_history(flat_id)
                df_hist = recalc_all_sequential(df_hist, df_serv, calc_config)
                save_history(df_hist, flat_id)
                st.success("Настройки сохранены, история пересчитана!")
                st.rerun()

    with st.expander("💰 Настроить услугу (Тариф, Место, Цвет, Название)", expanded=False):
        if not unique_services:
            st.caption("Нет добавленных услуг.")
        else:
            selected_service = st.selectbox("Какую услугу редактируем?", unique_services, key="service_selector")
            today_str = datetime.now().strftime("%Y-%m-%d")
            current_active, active_date_str = get_active_tariff_and_date(df_serv, selected_service, today_str)
            current_order, current_color = get_service_meta(df_serv, selected_service)
            st.info(f"Действует сегодня: `{current_active}`")
            with st.form("edit_tariff_form"):
                st.markdown("**Название услуги:**")
                st.markdown(f"Текущее: `{selected_service}`")
                new_name = st.text_input("Новое название", value=selected_service, key=f"rename_{selected_service}")
                new_tariff_val = st.text_input("Стоимость тарифа (число или ступени):", value=str(current_active), key=f"tariff_{selected_service}")
                try:
                    default_date = datetime.strptime(active_date_str, "%Y-%m-%d")
                except:
                    default_date = datetime.now()
                start_date_input = st.date_input("С какой даты действует этот тариф?", value=default_date, key=f"date_{selected_service}")
                st.markdown("---")
                st.markdown("**Внешний вид колонки:**")
                new_order_val = st.slider("Позиция на экране (чем меньше, тем левее)", min_value=1, max_value=20, value=int(current_order), key=f"order_{selected_service}")
                new_color_val = st.color_picker("Цвет карточки заголовка:", value=current_color, key=f"color_{selected_service}")
                if st.form_submit_button("💾 Сохранить изменения"):
                    name_changed = (new_name != selected_service)
                    if name_changed:
                        all_names = df_serv["Услуга"].unique().tolist()
                        if new_name in all_names:
                            st.error("Услуга с таким названием уже существует!")
                            st.stop()
                        else:
                            df_serv.loc[df_serv["Услуга"] == selected_service, "Услуга"] = new_name
                            df_hist = get_history(flat_id)
                            df_hist.loc[df_hist["Услуга"] == selected_service, "Услуга"] = new_name
                            save_history(df_hist, flat_id)
                            new_calc = {}
                            for k, v in calc_config.items():
                                if k == selected_service:
                                    new_calc[new_name] = v
                                else:
                                    new_calc[k] = [new_name if x == selected_service else x for x in v]
                            save_calc_config(new_calc, flat_id)
                            calc_config = new_calc
                            selected_service = new_name
                    df_serv.loc[df_serv["Услуга"] == selected_service, "Порядок"] = new_order_val
                    df_serv.loc[df_serv["Услуга"] == selected_service, "Цвет"] = str(new_color_val)
                    formatted_start_date = start_date_input.strftime("%Y-%m-%d")
                    mask = (df_serv["Услуга"] == selected_service) & (df_serv["Дата_начала"] == formatted_start_date)
                    if mask.any():
                        df_serv.loc[mask, "Тариф"] = str(new_tariff_val)
                    else:
                        new_entry = {
                            "Услуга": selected_service, "Тариф": str(new_tariff_val), "Дата_начала": formatted_start_date,
                            "Порядок": new_order_val, "Цвет": str(new_color_val)
                        }
                        df_serv = pd.concat([df_serv, pd.DataFrame([new_entry])], ignore_index=True)
                    save_services(df_serv, flat_id)
                    df_hist = get_history(flat_id)
                    df_hist = recalc_all_sequential(df_hist, df_serv, calc_config)
                    save_history(df_hist, flat_id)
                    st.success("Настройки сохранены, история пересчитана!")
                    st.rerun()

    with st.expander("📅 Управление тарифами (сетка и удаление)", expanded=False):
        sorted_tariffs = df_serv.sort_values(by=["Порядок", "Услуга", "Дата_начала"], ascending=[True, True, False]).reset_index(drop=True)
        st.dataframe(sorted_tariffs, use_container_width=True)
        st.markdown("**Удалить тариф:**")
        tariff_options = [f"{row['Услуга']} | {row['Дата_начала']} | {row['Тариф']}" for _, row in sorted_tariffs.iterrows()]
        if tariff_options:
            selected_tariff_str = st.selectbox("Выберите тариф для удаления:", tariff_options, key="del_tariff_select")
            if st.button("🗑️ Удалить выбранный тариф"):
                parts = selected_tariff_str.split(" | ")
                if len(parts) == 3:
                    service, date, tariff = parts
                    idx_drop = df_serv[(df_serv["Услуга"] == service) & (df_serv["Дата_начала"] == date) & (df_serv["Тариф"] == tariff)].index
                    if len(idx_drop) > 0:
                        df_serv = df_serv.drop(idx_drop)
                        save_services(df_serv, flat_id)
                        df_hist = get_history(flat_id)
                        df_hist = recalc_all_sequential(df_hist, df_serv, calc_config)
                        save_history(df_hist, flat_id)
                        st.success("Тариф удалён, история пересчитана!")
                        st.rerun()

    with st.expander("➕ Создать новую услугу", expanded=False):
        with st.form("add_new_service_form", clear_on_submit=True):
            new_name = st.text_input("Название новой услуги:")
            new_tariff_raw = st.text_input("Начальный тариф:")
            new_val = st.number_input("Стартовые показания счетчика", min_value=0.0, step=1.0)
            start_date_new = st.date_input("Дата запуска услуги", datetime.now())
            new_order_fresh = st.slider("Позиция на экране", min_value=1, max_value=20, value=5)
            new_color_fresh = st.color_picker("Цвет карточки заголовка:", value="#4CAF50")
            if st.form_submit_button("🚀 Создать услугу"):
                if new_name and new_tariff_raw:
                    if new_name in unique_services:
                        st.error("Уже существует!")
                    else:
                        new_row = {
                            "Услуга": new_name, "Тариф": str(new_tariff_raw), "Дата_начала": start_date_new.strftime("%Y-%m-%d"),
                            "Порядок": new_order_fresh, "Цвет": str(new_color_fresh)
                        }
                        df_serv = pd.concat([df_serv, pd.DataFrame([new_row])], ignore_index=True)
                        save_services(df_serv, flat_id)
                        df_hist = get_history(flat_id)
                        df_init_entry = pd.DataFrame([{
                            "Дата": start_date_new.strftime("%Y-%m-%d"), "Услуга": new_name,
                            "Расход": 0.0, "Тариф": "Старт", "Сумма_руб": 0.0, "Показания": new_val
                        }])
                        df_hist = pd.concat([df_hist, df_init_entry], ignore_index=True)
                        df_hist = recalc_all_sequential(df_hist, df_serv, calc_config)
                        save_history(df_hist, flat_id)
                        st.success("Услуга создана!")
                        st.rerun()

    with st.expander("🗑️ Удаление услуг", expanded=False):
        if unique_services:
            service_to_delete = st.selectbox("Удалить услугу полностью из системы:", unique_services, key="del_box")
            if st.button("❌ Удалить безвозвратно", type="primary"):
                df_serv = df_serv[df_serv["Услуга"] != service_to_delete]
                save_services(df_serv, flat_id)
                new_calc = {k: v for k, v in calc_config.items() if k != service_to_delete}
                for k in new_calc:
                    new_calc[k] = [s for s in new_calc[k] if s != service_to_delete]
                save_calc_config(new_calc, flat_id)
                calc_config = new_calc
                st.warning("Удалено.")
                st.rerun()

    # --- Резервное копирование ---
    with st.expander("💾 Резервное копирование (бэкап)", expanded=False):
        st.markdown("**Скачать бэкап текущей квартиры:**")
        backup_data = create_backup_zip(flat_id)
        st.download_button("📥 Скачать бэкап (ZIP)", data=backup_data,
                           file_name=f"backup_{flat_id}_{datetime.now():%Y%m%d_%H%M%S}.zip",
                           mime="application/zip", use_container_width=True)

        st.markdown("---")
        st.markdown("**Восстановить бэкап**")
        restore_mode = st.radio("Способ восстановления:",
                                ["Загрузить ZIP-архив", "Вставить тексты CSV"],
                                index=0, key="restore_mode")

        if restore_mode == "Загрузить ZIP-архив":
            uploaded_zip = st.file_uploader("Выберите ZIP-архив", type="zip", key="backup_zip_uploader")
            if uploaded_zip is not None:
                if st.button("🔄 Восстановить из ZIP"):
                    try:
                        with zipfile.ZipFile(uploaded_zip, "r") as zf:
                            required = ["services.csv", "history.csv", "calc_config.csv"]
                            if not all(f in zf.namelist() for f in required):
                                st.error("В архиве отсутствуют необходимые файлы (services.csv, history.csv, calc_config.csv)")
                            else:
                                zf.extractall(path=".")
                                for f in required:
                                    if os.path.exists(f):
                                        target = f.replace(".csv", f"_{flat_id}.csv")
                                        if os.path.exists(target):
                                            os.remove(target)
                                        os.rename(f, target)
                                if "flat_info.txt" in zf.namelist():
                                    with open("flat_info.txt", "r", encoding="utf-8-sig") as f:
                                        new_name = f.read().strip()
                                    if new_name:
                                        flats_df = get_flats()
                                        flats_df.loc[flats_df["ID"] == flat_id, "Название"] = new_name
                                        save_flats(flats_df)
                                if "notes.txt" in zf.namelist():
                                    with open("notes.txt", "r", encoding="utf-8-sig") as f:
                                        notes_text = f.read()
                                    save_notes(flat_id, notes_text)
                                df_serv = get_services(flat_id)
                                df_hist = get_history(flat_id)
                                calc_config = get_calc_config(flat_id)
                                df_hist = recalc_all_sequential(df_hist, df_serv, calc_config)
                                save_history(df_hist, flat_id)
                                st.success("Данные успешно восстановлены! Страница перезагрузится.")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при восстановлении ZIP: {e}")
        else:
            st.info("Вставьте содержимое CSV-файлов вручную. Название квартиры и заметки — опционально.")
            txt_serv = st.text_area("services.csv", height=150, key=f"restore_serv_{flat_id}")
            txt_hist = st.text_area("history.csv", height=150, key=f"restore_hist_{flat_id}")
            txt_calc = st.text_area("calc_config.csv", height=100, key=f"restore_calc_{flat_id}")
            txt_flat_name = st.text_area("flat_info.txt (опционально)", height=70, key=f"restore_flatname_{flat_id}")
            txt_notes = st.text_area("notes.txt (опционально)", height=100, key=f"restore_notes_{flat_id}")
            if txt_serv and txt_hist and txt_calc:
                if st.button("🔄 Восстановить из текста", key=f"restore_btn_{flat_id}"):
                    try:
                        df_serv_rest = pd.read_csv(io.StringIO(txt_serv), dtype={"Тариф": str, "Услуга": str})
                        df_hist_rest = pd.read_csv(io.StringIO(txt_hist), dtype={"Услуга": str, "Тариф": str})
                        df_calc_rest = pd.read_csv(io.StringIO(txt_calc), dtype=str)
                        if not {"Услуга","Тариф","Дата_начала","Порядок","Цвет"}.issubset(df_serv_rest.columns):
                            st.error("services.csv некорректен.")
                        elif not {"Дата","Услуга","Расход","Тариф","Сумма_руб","Показания"}.issubset(df_hist_rest.columns):
                            st.error("history.csv некорректен.")
                        elif not {"Расчётная услуга","Исходная услуга"}.issubset(df_calc_rest.columns):
                            st.error("calc_config.csv некорректен.")
                        else:
                            save_services(df_serv_rest, flat_id)
                            save_history(df_hist_rest, flat_id)
                            restored_calc = {}
                            for _, row in df_calc_rest.iterrows():
                                t = row["Расчётная услуга"].strip()
                                s = row["Исходная услуга"].strip()
                                restored_calc.setdefault(t, []).append(s)
                            save_calc_config(restored_calc, flat_id)
                            if txt_flat_name.strip():
                                flats_df = get_flats()
                                flats_df.loc[flats_df["ID"] == flat_id, "Название"] = txt_flat_name.strip()
                                save_flats(flats_df)
                            if txt_notes.strip():
                                save_notes(flat_id, txt_notes.strip())
                            st.success("Данные восстановлены!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка: {e}")

# ====================== ВВОД ПОКАЗАНИЙ ======================
st.markdown("### 📝 Внести новые показания за период")
if not unique_services:
    st.info("Список услуг пуст.")
else:
    # CSS для выравнивания высоты полей ввода
    st.markdown("""
        <style>
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextInput"] input {
            height: 40px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.form("main_meters_top_form"):
        date_input = st.date_input("Выбор расчетного периода (Дата)", datetime.now())
        formatted_date = date_input.strftime("%Y-%m-%d")
        st.markdown("---")
        num_services = len(unique_services)
        cols = st.columns(num_services)
        user_inputs = {}
        calculated_services = list(calc_config.keys())

        for idx, name in enumerate(unique_services):
            with cols[idx]:
                active_tariff_str, _ = get_active_tariff_and_date(df_serv, name, formatted_date)
                last_val = get_last_meter_value(df_hist, name)
                _, s_color = get_service_meta(df_serv, name)

                # Заголовок с цветной полосой и фиксированной высотой
                if ":" in active_tariff_str:
                    tariff_display = f'''Динам. <details style="display:inline;">
                        <summary style="display:inline; cursor:pointer; color:#555;">ⓘ</summary>
                        <span style="font-size:0.9em;">{active_tariff_str}</span>
                    </details>'''
                else:
                    tariff_display = active_tariff_str

                html_block = f"""
                <div style="height: 120px; overflow-y: auto; margin-bottom: 5px; border-left: 5px solid {s_color}; padding-left: 10px;">
                    <h5 style="margin: 0 0 4px 0; padding: 0; color: inherit;">{name}</h5>
                    <span style="font-size: 13px; color: inherit;"><b>Тариф:</b> {tariff_display}</span>
                </div>
                """
                st.html(html_block)

                # Поле ввода
                if name in calculated_services:
                    # Скрытый текст для выравнивания высоты с number_input
                    st.markdown("<span style='visibility:hidden; font-size:14px;'>Ввод (было: 0.0)</span>", unsafe_allow_html=True)
                    source_names = ", ".join([s.split('(')[0].strip() for s in calc_config[name]])
                    st.text_input("", value=source_names, disabled=True,
                                  label_visibility="collapsed", key=f"disabled_{name}_{flat_id}")
                    new_val = last_val
                else:
                    new_val = st.number_input(
                        f"Ввод (было: {last_val})",
                        min_value=0.0,
                        value=last_val,
                        step=1.0,
                        key=f"input_{name}_{flat_id}"
                    )
                user_inputs[name] = {"new": new_val, "old": last_val, "tariff": active_tariff_str}

        st.markdown("---")
        submit_btn = st.form_submit_button("💾 Рассчитать расход и сохранить в архив", type="primary", use_container_width=True)

        if submit_btn:
            reset_services = []
            for name, data in user_inputs.items():
                if name not in calculated_services and data["new"] < data["old"]:
                    reset_services.append(name)
            if reset_services:
                st.session_state.reset_warning = True
                st.session_state.reset_services = reset_services

            df_hist_updated = get_history(flat_id)
            df_hist_updated = df_hist_updated[df_hist_updated["Дата"] != formatted_date]

            new_rows = []
            for name, data in user_inputs.items():
                if name in calculated_services:
                    new_rows.append({
                        "Дата": formatted_date, "Услуга": name,
                        "Расход": 0.0, "Тариф": "", "Сумма_руб": 0.0, "Показания": 0.0
                    })
                else:
                    new_rows.append({
                        "Дата": formatted_date, "Услуга": name,
                        "Расход": 0.0, "Тариф": "", "Сумма_руб": 0.0, "Показания": data["new"]
                    })

            df_new = pd.DataFrame(new_rows)
            df_hist_updated = pd.concat([df_hist_updated, df_new], ignore_index=True)
            df_hist_updated = recalc_all_sequential(df_hist_updated, df_serv, calc_config)
            save_history(df_hist_updated, flat_id)

            st.success("Данные добавлены и пересчитаны!")
            st.rerun()

# ====================== АНАЛИТИКА ======================
st.markdown("---")
st.markdown("## 📈 Архив записей и аналитика затрат")

if df_hist.empty:
    st.info("История платежей пуста.")
else:
    try:
        pivot_sum = df_hist.pivot_table(index="Дата", columns="Услуга", values="Сумма_руб", aggfunc="sum").fillna(0)
        pivot_meter = df_hist.pivot_table(index="Дата", columns="Услуга", values="Показания", aggfunc="max").fillna(0)
        pivot_cons = df_hist.pivot_table(index="Дата", columns="Услуга", values="Расход", aggfunc="sum").fillna(0)

        for srv in unique_services:
            if srv not in pivot_sum.columns:
                pivot_sum[srv] = 0.0
            if srv not in pivot_meter.columns:
                pivot_meter[srv] = 0.0
            if srv not in pivot_cons.columns:
                pivot_cons[srv] = 0.0

        result_df = pd.DataFrame(index=pivot_sum.index)
        flat_columns = []
        result_df["ИТОГО к оплате"] = 0.0
        flat_columns.append("ИТОГО к оплате")

        calculated_services = list(calc_config.keys())
        for srv in unique_services:
            short_name = srv.split('(')[0].strip() if '(' in srv else srv
            if srv in calculated_services:
                meter_col = f"{short_name} (изм.)"
                result_df[meter_col] = pivot_cons[srv]
            else:
                meter_col = f"{short_name} (пок.)"
                result_df[meter_col] = pivot_meter[srv]

            sum_col = f"{short_name} (сумма)"
            result_df[sum_col] = pivot_sum[srv]
            flat_columns.append(meter_col)
            flat_columns.append(sum_col)
            result_df["ИТОГО к оплате"] += pivot_sum[srv]

        result_df = result_df[flat_columns].sort_index(ascending=False)

        st.markdown("**Сводная таблица затрат и показаний:**")
        st.dataframe(result_df, use_container_width=True)

        available_dates = result_df.index.tolist()
        if available_dates:
            col1, col2 = st.columns([2,1])
            with col1:
                date_to_delete = st.selectbox("Выберите дату для удаления всех записей:", available_dates, key="delete_date_select")
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if "confirm_delete_date" not in st.session_state:
                    st.session_state.confirm_delete_date = None

                if st.button("🗑️ Удалить записи за эту дату", key="delete_date_btn"):
                    st.session_state.confirm_delete_date = date_to_delete

                if st.session_state.confirm_delete_date == date_to_delete:
                    st.warning(f"Вы уверены, что хотите удалить ВСЕ записи за {date_to_delete}?")
                    if st.button("✅ Подтвердить удаление", key="confirm_delete_btn"):
                        df_hist_updated = df_hist[df_hist["Дата"] != date_to_delete]
                        df_hist_updated = recalc_all_sequential(df_hist_updated, df_serv, calc_config)
                        save_history(df_hist_updated, flat_id)
                        st.success(f"Записи за {date_to_delete} удалены и история пересчитана!")
                        st.session_state.confirm_delete_date = None
                        st.rerun()

        plot_data = pivot_sum[unique_services].copy()
        plot_data.columns = [col.split('(')[0].strip() for col in plot_data.columns]
        plot_data = plot_data.reset_index().melt(id_vars="Дата", var_name="Услуга", value_name="Сумма")
        color_dict = {}
        for srv in unique_services:
            _, color = get_service_meta(df_serv, srv)
            color_dict[srv.split('(')[0].strip()] = color
        chart = alt.Chart(plot_data).mark_bar().encode(
            x=alt.X("Дата:O"), y=alt.Y("Сумма:Q"),
            color=alt.Color("Услуга:N", scale=alt.Scale(domain=list(color_dict.keys()), range=list(color_dict.values())),
                           legend=alt.Legend(title="Услуга"), sort=list(color_dict.keys()))
        ).properties(width='container', height=400)
        st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        st.markdown("**Текущие показания счетчиков:**")
        current_meters = []
        for srv in unique_services:
            last_val = get_last_meter_value(df_hist, srv)
            if not df_hist.empty and srv in df_hist["Услуга"].values:
                last_date = df_hist[df_hist["Услуга"] == srv].sort_values("Дата", ascending=False).iloc[0]["Дата"]
            else:
                last_date = "Нет данных"
            short_name = srv.split('(')[0].strip()
            current_meters.append({"Услуга": short_name, "Последние пок.": last_val, "Дата обновления": last_date})
        st.dataframe(pd.DataFrame(current_meters), use_container_width=True)

    except Exception as e:
        st.error(f"Ошибка при построении аналитики: {e}")
        st.dataframe(df_hist.sort_values("Дата", ascending=False), use_container_width=True)

    st.markdown("---")
    download_format = st.radio("Формат скачивания архива:", ["CSV (UTF-8 с BOM)", "Excel (XLSX)"], index=0)
    if download_format == "CSV (UTF-8 с BOM)":
        csv_hist = df_hist.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Скачать архив (CSV)", data=csv_hist, file_name=f"history_{flat_id}_{datetime.now():%Y%m%d}.csv", mime="text/csv")
    else:
        try:
            import openpyxl
            output = pd.ExcelWriter('temp.xlsx', engine='openpyxl')
            df_hist.to_excel(output, index=False, sheet_name='История')
            output.close()
            with open('temp.xlsx', 'rb') as f:
                xlsx_data = f.read()
            st.download_button("📥 Скачать архив (Excel)", data=xlsx_data, file_name=f"history_{flat_id}_{datetime.now():%Y%m%d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except ImportError:
            st.error("Установите openpyxl: pip install openpyxl")

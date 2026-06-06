# В конце аналитики заменить radio и download_button на:
st.markdown("---")
st.markdown("**Скачать историю:**")
col_csv, col_xlsx = st.columns(2)
with col_csv:
    csv_hist = df_hist.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Скачать CSV",
        data=csv_hist,
        file_name=f"history_{flat_id}_{datetime.now():%Y%m%d}.csv",
        mime="text/csv",
        use_container_width=True
    )
with col_xlsx:
    try:
        import openpyxl
        output = pd.ExcelWriter('temp.xlsx', engine='openpyxl')
        df_hist.to_excel(output, index=False, sheet_name='История')
        output.close()
        with open('temp.xlsx', 'rb') as f:
            xlsx_data = f.read()
        st.download_button(
            label="📥 Скачать Excel",
            data=xlsx_data,
            file_name=f"history_{flat_id}_{datetime.now():%Y%m%d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except ImportError:
        st.error("Установите openpyxl: pip install openpyxl")

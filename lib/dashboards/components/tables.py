from dash import dash_table


def create_dash_table_from_dataframe(dataframe):
    column_renames = {
        'objective_func': 'значение целевой функции',
        'trial': 'номер испытания',
        'index': 'индекс точки'
    }


    columns = []
    for col_id in dataframe.columns:
        display_name = column_renames.get(col_id, col_id) 
        
        columns.append({
            "name": display_name, 
            "id": col_id
        })

    return dash_table.DataTable(
        dataframe.to_dict('records'),
        columns,
        filter_action="native",
        id='datatable-interactivity',
        sort_action="native",
        row_selectable="multi",
        selected_rows=[],
        sort_mode="multi",
        page_size=12
    )

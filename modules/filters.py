import pandas as pd

def filter_in(worksheet, df, f):
    col_idx = df.columns.get_loc(f"{f}_text")
    worksheet.filter_column(col_idx, "x == 1")

    for row_num in (df.index[(df[f"{f}_text"] == 0)].tolist()):
        worksheet.set_row(row_num + 1, options={'hidden': True})

def filter_out(worksheet, df, f):
    col_idx = df.columns.get_loc(f"{f}_text")
    worksheet.filter_column(col_idx, "x == 0")

    for row_num in (df.index[(df[f"{f}_text"] == 1)].tolist()):
        worksheet.set_row(row_num + 1, options={'hidden': True})

def filter_between(worksheet, df, f, p_min, p_max):
    col_idx = df.columns.get_loc(f)
    worksheet.filter_column(col_idx, f'x > {p_min} and x < {p_max}')

    for row_num in df[(df[f] < p_min) | (df[f] > p_max)].index.tolist():
        worksheet.set_row(row_num + 1, options={'hidden': True})


def main(txt_filters: list, price_filter: tuple, surface_filter: tuple, txt_hide: bool):
    df = pd.read_csv("data/houses.csv")

    writer = pd.ExcelWriter("data/houses.xlsx")
    df.to_excel(writer, index=False, sheet_name="real_estate")

    workbook = writer.book
    worksheet = writer.sheets['real_estate']


    worksheet.autofilter(0, 0, df.shape[0], df.shape[1]-1)
    header_format = workbook.add_format({
        'bold': True,
        'font_name': 'Calibri',
        'text_wrap': False,
        'valign': 'top',
        'border': 1})
    # Write the column headers with the defined format.
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    if len(txt_filters)>0:
        for f in txt_filters:
            filter_in(worksheet, df, f)
    filter_out(worksheet, df, "NO")

    if price_filter is not None:
        filter_between(worksheet, df, 'price', price_filter[0], price_filter[1])
    if surface_filter is not None:
        filter_between(worksheet, df, 'surface', surface_filter[0], surface_filter[1])


    # Auto-adjust columns' width
    for column in df:
        column_width = max(df[column].astype(str).map(len).max(), len(column)+3)
        col_idx = df.columns.get_loc(column)
        writer.sheets['real_estate'].set_column(col_idx, col_idx, column_width)

    if txt_hide:
        for col in [c for c in df.columns if c.endswith("_text")]:
            col_idx = df.columns.get_loc(col)
            writer.sheets['real_estate'].set_column(col_idx, col_idx, None, options={'hidden': True})



    writer.save()
import xlsxwriter
from django.db.models import QuerySet
from typing import List, Optional, Any
from datetime import datetime
import os


class ExcelExporter:
    def __init__(self, filename: str = None):
        self.filename = filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self.rows_data = []
        self.headers = []
        self.column_widths = {}
        
    def _format_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)
    
    def _update_column_width(self, col_num: int, value: str):
        width = min(len(value) + 2, 50)
        if col_num not in self.column_widths:
            self.column_widths[col_num] = width
        else:
            self.column_widths[col_num] = max(self.column_widths[col_num], width)
    
    def add_headers(self, headers: List[str]):
        self.headers = headers
        for col_num, header in enumerate(headers):
            self._update_column_width(col_num, header)
    
    def add_row(self, values: List[Any]):
        row_values = [self._format_value(v) for v in values]
        self.rows_data.append(row_values)
        for col_num, value in enumerate(row_values):
            self._update_column_width(col_num, value)
    
    def add_queryset(self, queryset: QuerySet, fields: List[str], headers: Optional[List[str]] = None):
        if not headers:
            headers = [field.replace('_', ' ').title() for field in fields]
        
        self.add_headers(headers)
        
        for obj in queryset:
            row_values = []
            for field in fields:
                try:
                    value = obj
                    for attr in field.split('__'):
                        value = getattr(value, attr, None)
                    row_values.append(value)
                except AttributeError:
                    row_values.append(None)
            self.add_row(row_values)
    
    def save(self, filepath: str = None) -> str:
        output_path = filepath or os.path.join('exports', self.filename)
        os.makedirs(os.path.dirname(output_path) or 'exports', exist_ok=True)
        
        workbook = xlsxwriter.Workbook(output_path)
        worksheet = workbook.add_worksheet()
        
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4472C4',
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1
        })
        
        for col_num, header in enumerate(self.headers):
            worksheet.write(0, col_num, header, header_format)
        
        for row_num, row_values in enumerate(self.rows_data, start=1):
            for col_num, value in enumerate(row_values):
                worksheet.write(row_num, col_num, value, cell_format)
        
        for col_num, width in self.column_widths.items():
            worksheet.set_column(col_num, col_num, width)
        
        workbook.close()
        return output_path

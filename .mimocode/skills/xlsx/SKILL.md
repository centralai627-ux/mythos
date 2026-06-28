---
name: xlsx
description: Use when user wants to create, read, edit, or analyze Excel spreadsheets (.xlsx, .csv, .tsv) in Mythos
---

# XLSX Processing for Mythos

## Overview

Guide for Excel spreadsheet operations using Python (pandas, openpyxl).

## Quick Reference

| Task | Best Tool |
|------|-----------|
| Data analysis | pandas |
| Create/edit with formulas | openpyxl |
| Simple data export | pandas |
| Complex formatting | openpyxl |

## Python: pandas

### Read Excel
```python
import pandas as pd

# Read single sheet
df = pd.read_excel('file.xlsx')

# Read all sheets
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)

# Read specific columns
df = pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])

# Preview
df.head()
df.info()
df.describe()
```

### Write Excel
```python
import pandas as pd

df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
df.to_excel('output.xlsx', index=False)

# Write to specific sheet
with pd.ExcelWriter('output.xlsx') as writer:
    df1.to_excel(writer, sheet_name='Sheet1', index=False)
    df2.to_excel(writer, sheet_name='Sheet2', index=False)
```

### Data Cleaning
```python
import pandas as pd

# Handle missing values
df.dropna()  # Remove rows with NaN
df.fillna(0)  # Fill NaN with 0

# Remove duplicates
df.drop_duplicates()

# Rename columns
df.rename(columns={'old': 'new'})

# Filter
df[df['column'] > 100]
```

## Python: openpyxl

### Create with Formulas
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# Headers
sheet['A1'] = 'Product'
sheet['B1'] = 'Sales'
sheet['C1'] = 'Total'

# Data
sheet['A2'] = 'Item 1'
sheet['B2'] = 100
sheet['A3'] = 'Item 2'
sheet['B3'] = 200

# Formula (NOT hardcoded!)
sheet['C4'] = '=SUM(B2:B3)'

# Formatting
sheet['A1'].font = Font(bold=True)
sheet['A1'].fill = PatternFill('solid', fgColor='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# Column width
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### Edit Existing
```python
from openpyxl import load_workbook

wb = load_workbook('existing.xlsx')
sheet = wb.active

# Modify cells
sheet['A1'] = 'New Value'

# Add new sheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

### Read with Formulas
```python
from openpyxl import load_workbook

# Read calculated values (not formula strings)
wb = load_workbook('file.xlsx', data_only=True)
sheet = wb.active

# Get calculated value
value = sheet['C4'].value  # Returns calculated result
```

## Financial Model Standards

### Color Coding
| Color | Meaning |
|-------|---------|
| Blue text | Hardcoded inputs |
| Black text | Formulas |
| Green text | Links to other worksheets |
| Red text | External links |
| Yellow background | Key assumptions |

### Number Formatting
```python
from openpyxl.styles import numbers

# Currency
cell.number_format = '$#,##0'

# Percentage
cell.number_format = '0.0%'

# Negative in parentheses
cell.number_format = '#,##0;(#,##0);"-"'
```

## Common Tasks

### Merge Multiple Excel Files
```python
import pandas as pd
import glob

files = glob.glob('*.xlsx')
all_data = []

for f in files:
    df = pd.read_excel(f)
    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)
combined.to_excel('combined.xlsx', index=False)
```

### Create Charts
```python
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference

wb = Workbook()
sheet = wb.active

# Add data
sheet['A1'] = 'Category'
sheet['B1'] = 'Value'
sheet['A2'] = 'A'
sheet['B2'] = 10
sheet['A3'] = 'B'
sheet['B3'] = 20

# Create chart
chart = BarChart()
chart.title = "My Chart"
data = Reference(sheet, min_col=2, min_row=1, max_row=3)
cats = Reference(sheet, min_col=1, min_row=2, max_row=3)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
sheet.add_chart(chart, "D1")

wb.save('chart.xlsx')
```

### Export to CSV
```python
import pandas as pd

df = pd.read_excel('input.xlsx')
df.to_csv('output.csv', index=False)
```

## Dependencies

```bash
pip install pandas openpyxl
```

## Mythos-Specific

Use XLSX skill when:
- User mentions Excel, spreadsheets, .xlsx, .csv files
- User wants to analyze tabular data
- User wants to create reports with charts
- User wants to process data from spreadsheets
- User mentions "tabel", "data", "laporan" (Indonesian)

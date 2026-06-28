---
name: docx
description: Use when user wants to create, read, edit, or manipulate Word documents (.docx files) in Mythos
---

# DOCX Processing for Mythos

## Overview

Guide for Word document operations using JavaScript (docx-js) or Python (python-docx).

## Quick Reference

| Task | Approach |
|------|----------|
| Read/analyze content | python-docx or pandoc |
| Create new document | docx-js (Node.js) or python-docx |
| Edit existing document | Unpack XML, edit, repack |

## Python: python-docx

### Read Document
```python
from docx import Document

doc = Document("document.docx")

# Read paragraphs
for para in doc.paragraphs:
    print(para.text)

# Read tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text)
```

### Create Document
```python
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Title
title = doc.add_heading('Document Title', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Heading
doc.add_heading('Section 1', level=1)

# Paragraph
doc.add_paragraph('This is a paragraph.')

# List
doc.add_paragraph('Item 1', style='List Bullet')
doc.add_paragraph('Item 2', style='List Bullet')

# Table
table = doc.add_table(rows=3, cols=3)
for i, row in enumerate(table.rows):
    for j, cell in enumerate(row.cells):
        cell.text = f'Cell {i},{j}'

# Add image
doc.add_picture('image.png', width=Inches(4))

# Save
doc.save('output.docx')
```

### Edit Document
```python
from docx import Document

doc = Document('existing.docx')

# Add paragraph
doc.add_paragraph('New content')

# Modify existing paragraph
for para in doc.paragraphs:
    if 'old text' in para.text:
        para.text = para.text.replace('old text', 'new text')

doc.save('modified.docx')
```

## JavaScript: docx-js

### Create Document
```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, PageNumber } = require('docx');
const fs = require('fs');

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 }, // US Letter
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({ children: [new TextRun("Header")] })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] })]
        })]
      })
    },
    children: [
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("Title")]
      }),
      new Paragraph({
        children: [new TextRun("Body text")]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("document.docx", buffer);
});
```

### Tables
```javascript
const { Table, TableRow, TableCell, BorderStyle, WidthType, ShadingType } = require('docx');

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [4680, 4680],
  rows: [
    new TableRow({
      children: [
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA },
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
          children: [new Paragraph({ children: [new TextRun("Header")] })]
        }),
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA },
          children: [new Paragraph({ children: [new TextRun("Value")] })]
        })
      ]
    })
  ]
})
```

## Command Line Tools

### pandoc (text extraction)
```bash
pandoc document.docx -o output.md
```

### Convert .doc to .docx
```bash
libreoffice --headless --convert-to docx document.doc
```

## Dependencies

```bash
# Python
pip install python-docx

# JavaScript
npm install -g docx
```

## Mythos-Specific

Use DOCX skill when:
- User mentions Word documents or .docx files
- User wants to create reports, memos, letters
- User wants to extract content from Word files
- User wants to convert content to professional documents

#!/usr/bin/env python3
"""
Grade Report PDF Generator

Generates individual grade report pages for each student from a CSV file.
One PDF file containing one page per student with their name, SID, email, and grade table.

Usage:
    python generate_grade_reports.py input.csv output.pdf
    python generate_grade_reports.py input.csv output.pdf --columns "hw1,hw2,midterm,final"
    python generate_grade_reports.py input.csv output.pdf --columns "T1,T2,Final" --comment "Great work this quarter!"
"""

import argparse
import csv
import sys
from typing import List, Dict, Tuple, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def find_column_case_insensitive(headers: List[str], patterns: List[str]) -> Optional[int]:
    """Find a column index by matching against multiple patterns (case-insensitive)."""
    headers_lower = [h.lower().strip() for h in headers]
    for pattern in patterns:
        pattern_lower = pattern.lower()
        if pattern_lower in headers_lower:
            return headers_lower.index(pattern_lower)
    return None


def detect_student_info_columns(headers: List[str]) -> Dict[str, int]:
    """Auto-detect student information columns from CSV headers."""
    detection_patterns = {
        'first_name': ['first name', 'firstname', 'first_name', 'fname'],
        'last_name': ['last name', 'lastname', 'last_name', 'lname'],
        'sid': ['sid', 'student id', 'student_id', 'id', 'student number'],
        'email': ['email', 'e-mail', 'e_mail', 'mail']
    }
    
    detected = {}
    for field, patterns in detection_patterns.items():
        idx = find_column_case_insensitive(headers, patterns)
        if idx is not None:
            detected[field] = idx
    
    return detected


def format_score(score: str) -> str:
    """Format numerical scores to 2 decimal places, leave non-numeric values as-is."""
    if not score or not score.strip():
        return score
    
    try:
        # Try to convert to float
        num_score = float(score)
        # Format to 2 decimal places
        return f"{num_score:.2f}"
    except (ValueError, TypeError):
        # Not a number, return as-is
        return score


def calculate_max_columns(page_width: float, left_margin: float, right_margin: float, 
                         min_col_width: float = 0.8, comment_lines: int = 0) -> int:
    """Calculate maximum number of columns that can fit on a page.
    
    Args:
        page_width: Width of the page
        left_margin: Left margin
        right_margin: Right margin
        min_col_width: Minimum column width in inches
        comment_lines: Number of lines of comment text (affects available height)
    """
    available_width = page_width - left_margin - right_margin
    # Reserve some width for the column name (first column)
    column_name_width = 1.5 * inch
    available_for_data = available_width - column_name_width
    max_cols = int(available_for_data / (min_col_width * inch))
    
    # Reduce max columns based on comment space needed
    # Roughly: every 3 lines of comment reduces capacity by 1 column
    # (since more vertical space means less room for table rows)
    if comment_lines > 0:
        reduction = min(2, comment_lines // 3)
        max_cols = max(1, max_cols - reduction)
    
    return max(1, max_cols)


def create_student_page_elements(student_data: Dict[str, str], 
                                grade_columns: List[str],
                                styles: dict,
                                comment: Optional[str] = None) -> List:
    """Create PDF elements for a single student page."""
    elements = []
    
    # Header with student information
    header_style = ParagraphStyle(
        'StudentHeader',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#003660'),
        spaceAfter=6
    )
    
    info_style = ParagraphStyle(
        'StudentInfo',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=3
    )
    
    # Create header layout: student info on left, comment box on right (if provided)
    if comment:
        # Create student info paragraphs
        name = f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
        student_info_paras = [Paragraph(f"<b>{name}</b>", header_style)]
        
        if 'sid' in student_data:
            student_info_paras.append(Paragraph(f"<b>SID:</b> {student_data['sid']}", info_style))
        if 'email' in student_data:
            student_info_paras.append(Paragraph(f"<b>Email:</b> {student_data['email']}", info_style))
        
        # Combine student info into a single cell
        student_info_combined = []
        for para in student_info_paras:
            student_info_combined.append(para)
            student_info_combined.append(Spacer(1, 2))
        
        # Create comment box
        comment_style = ParagraphStyle(
            'CommentStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=12
        )
        
        comment_para = Paragraph(comment, comment_style)
        comment_cell = Table([[comment_para]], colWidths=[2.5*inch])
        comment_cell.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Create header table with student info on left, comment on right
        header_table_data = [[student_info_combined, comment_cell]]
        header_table = Table(header_table_data, colWidths=[4*inch, 2.75*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(header_table)
    else:
        # No comment - use simple layout
        name = f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
        elements.append(Paragraph(f"<b>{name}</b>", header_style))
        
        if 'sid' in student_data:
            elements.append(Paragraph(f"<b>SID:</b> {student_data['sid']}", info_style))
        if 'email' in student_data:
            elements.append(Paragraph(f"<b>Email:</b> {student_data['email']}", info_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Grade table
    if grade_columns:
        # Create table data
        table_data = [['Assignment', 'Score/Grade']]  # Header row
        
        for col in grade_columns:
            score = student_data.get(col, '')
            formatted_score = format_score(score)
            table_data.append([col, formatted_score])
        
        # Create table with styling
        table = Table(table_data, colWidths=[3.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003660')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ]))
        
        elements.append(table)
    
    return elements


def generate_pdf(csv_path: str, pdf_path: str, selected_columns: Optional[List[str]] = None,
                comment: Optional[str] = None):
    """Generate PDF grade reports from CSV file."""
    
    # Read CSV file
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    # Detect student info columns
    student_info_cols = detect_student_info_columns(headers)
    
    if not student_info_cols:
        print("Error: Could not detect student information columns.")
        print("Expected columns with names like: 'First Name', 'Last Name', 'SID', 'Email'")
        sys.exit(1)
    
    print(f"Detected student info columns:")
    for field, idx in student_info_cols.items():
        print(f"  {field}: {headers[idx]}")
    
    # Determine grade columns (all columns except student info)
    student_info_indices = set(student_info_cols.values())
    all_grade_columns = [headers[i] for i in range(len(headers)) 
                        if i not in student_info_indices and headers[i].strip()]
    
    print(f"\nFound {len(all_grade_columns)} grade columns")
    
    # Estimate comment lines for max column calculation
    comment_lines = 0
    if comment:
        # Estimate lines: roughly 60 characters per line in the comment box
        comment_lines = max(1, len(comment) // 60 + 1)
    
    # Handle column selection
    if selected_columns:
        # Validate selected columns
        invalid_cols = [col for col in selected_columns if col not in all_grade_columns]
        if invalid_cols:
            print(f"Error: Invalid column names: {', '.join(invalid_cols)}")
            print(f"\nAvailable grade columns:")
            for col in all_grade_columns:
                print(f"  - {col}")
            sys.exit(1)
        grade_columns = selected_columns
        print(f"Using {len(grade_columns)} selected columns")
    else:
        grade_columns = all_grade_columns
        
        # Check if all columns fit on one page
        max_cols = calculate_max_columns(letter[0], 0.75*inch, 0.75*inch, comment_lines=comment_lines)
        
        if len(grade_columns) > max_cols:
            print(f"\n{'='*70}")
            print(f"ERROR: Too many columns to fit on one page!")
            print(f"{'='*70}")
            print(f"Total grade columns: {len(grade_columns)}")
            print(f"Maximum columns per page: {max_cols}")
            print(f"\nAvailable grade columns:")
            for i, col in enumerate(all_grade_columns, 1):
                print(f"  {i:3d}. {col}")
            print(f"\nPlease re-run with the --columns flag to select specific columns:")
            print(f"  python {sys.argv[0]} {csv_path} {pdf_path} --columns \"col1,col2,col3\"")
            print(f"\nExample:")
            example_cols = ','.join(all_grade_columns[:min(5, max_cols)])
            print(f"  python {sys.argv[0]} {csv_path} {pdf_path} --columns \"{example_cols}\"")
            sys.exit(1)
    
    # Create PDF
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Process each student
    for row_idx, row in enumerate(rows):
        if not row or all(not cell.strip() for cell in row):
            continue  # Skip empty rows
        
        # Extract student data
        student_data = {}
        for field, col_idx in student_info_cols.items():
            if col_idx < len(row):
                student_data[field] = row[col_idx]
        
        # Extract grade data
        for i, header in enumerate(headers):
            if i not in student_info_indices and i < len(row):
                student_data[header] = row[i]
        
        # Create page elements for this student
        page_elements = create_student_page_elements(student_data, grade_columns, styles, comment)
        story.extend(page_elements)
        
        # Add page break except for last student
        if row_idx < len(rows) - 1:
            story.append(PageBreak())
    
    # Build PDF
    try:
        doc.build(story)
        print(f"\n✓ Successfully generated PDF: {pdf_path}")
        print(f"  Total students: {len(rows)}")
        print(f"  Columns included: {len(grade_columns)}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Generate grade report PDFs from CSV data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate PDF with all grade columns
  python generate_grade_reports.py grades.csv reports.pdf
  
  # Generate PDF with selected columns only
  python generate_grade_reports.py grades.csv reports.pdf --columns "hw1,hw2,midterm,final"
  
  # Add a comment to each report
  python generate_grade_reports.py grades.csv reports.pdf -c "T1,T2,Final" -m "Great work this quarter!"
        """
    )
    
    parser.add_argument('csv_file', help='Input CSV file path')
    parser.add_argument('pdf_file', help='Output PDF file path')
    parser.add_argument('--columns', '-c', 
                       help='Comma-separated list of grade columns to include',
                       type=str)
    parser.add_argument('--comment', '-m',
                       help='Optional comment text to display in top right corner of each report',
                       type=str)
    
    args = parser.parse_args()
    
    # Parse selected columns if provided
    selected_columns = None
    if args.columns:
        selected_columns = [col.strip() for col in args.columns.split(',')]
    
    generate_pdf(args.csv_file, args.pdf_file, selected_columns, args.comment)


if __name__ == '__main__':
    main()

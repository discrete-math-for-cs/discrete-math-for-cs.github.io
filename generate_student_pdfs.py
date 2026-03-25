#!/usr/bin/env python3
"""
Generate Student PDFs from LaTeX Template and CSV Data

This script generates personalized PDF files for each student by compiling a LaTeX
template with student-specific data from a CSV file. It uses pdflatex with runtime
parameters to avoid creating intermediate .tex files.

Usage:
    python generate_student_pdfs.py TEMPLATE.tex STUDENTS.csv [OPTIONS]

Required Arguments:
    TEMPLATE.tex          LaTeX template file with \\providecommand definitions for:
                         \\name, \\sequencenumber, and \\seat
    STUDENTS.csv          CSV file with columns: Student, Sequence, Notes
                         (also expected: ID, SIS User ID, SIS Login ID, Notes)

Optional Arguments:
    --suffix SUFFIX       Suffix for output filenames (default: CSE20W26)
    --output-dir DIR      Output directory for PDFs (default: current directory)
    --keep-aux            Keep auxiliary LaTeX files (.aux, .log, etc.)
    --extra           Generate additional PDFs that aren't customized to students (default: 0)

Examples:
    # Basic usage with default suffix
    python generate_student_pdfs.py exam_template.tex roster.csv

    # Custom suffix and output directory
    python generate_student_pdfs.py exam.tex students.csv --suffix CSE105S25 --output-dir pdfs/

    # Keep auxiliary files for debugging
    python generate_student_pdfs.py exam.tex students.csv --keep-aux

    # Generate 10 additional PDFs that aren't customized to students
    python generate_student_pdfs.py exam.tex students.csv --extra 10

Template Format:
    Your LaTeX template should start with:
    \\providecommand{\\name}{NAME}
    \\providecommand{\\sequencenumber}{SEQ NUM}
    \\providecommand{\\seat}{SEAT}
    
    The script will define these commands before the template is processed.

Output Format:
    Files are named: INDEX.StudentName.SUFFIX.pdf
    Where INDEX is zero-padded for alphabetical sorting (e.g., 001, 002, ..., 150)

Dependencies:
    - pdflatex must be installed and accessible in PATH
    - Python standard library only (csv, subprocess, argparse, os, sys, re, unicodedata)
"""

import csv
import subprocess
import argparse
import os
import sys
import re
import unicodedata
import shutil


def sanitize_filename(name):
    """
    Sanitize a student name for use in filenames.
    
    - Normalizes unicode characters (é -> e, ñ -> n, etc.)
    - Removes all spaces
    - Keeps only alphanumeric characters and hyphens
    - Returns a safe filename string
    
    Args:
        name (str): The student name to sanitize
        
    Returns:
        str: Sanitized filename-safe string
    """
    # Normalize unicode characters (NFKD decomposition)
    name = unicodedata.normalize('NFKD', name)
    # Encode to ASCII, ignore non-ASCII characters
    name = name.encode('ascii', 'ignore').decode('ascii')
    # Remove all non-alphanumeric except hyphens
    name = re.sub(r'[^a-zA-Z0-9\-]', '', name)
    # Ensure it's not empty
    if not name:
        name = "Student"
    return name


def escape_latex(text):
    """
    Escape special LaTeX characters in text.
    
    Handles: & % $ # _ { } ~ ^ \\
    
    Args:
        text (str): The text to escape
        
    Returns:
        str: LaTeX-safe escaped text
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Order matters! Backslash first
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    
    for old, new in replacements:
        text = text.replace(old, new)
    
    return text


def extract_latex_error(output):
    """
    Extract meaningful error messages from LaTeX output.
    
    Args:
        output (str): The stdout/stderr from pdflatex
        
    Returns:
        str: A concise error message
    """
    if not output:
        return "Unknown error (no output from pdflatex)"
    
    lines = output.split('\n')
    
    # Look for common LaTeX error patterns
    error_indicators = [
        '! ',  # LaTeX error marker
        'Error:',
        'Fatal error',
        'Emergency stop',
    ]
    
    error_lines = []
    for i, line in enumerate(lines):
        for indicator in error_indicators:
            if indicator in line:
                # Capture this line and a few following lines for context
                error_lines.extend(lines[i:min(i+5, len(lines))])
                break
        if len(error_lines) >= 10:  # Limit to avoid too much output
            break
    
    if error_lines:
        return '\n'.join(error_lines)
    
    # If no specific error found, return last 10 lines (often contains the issue)
    return '\n'.join(lines[-10:])


def check_pdflatex():
    """
    Check if pdflatex is installed and accessible.
    
    Returns:
        bool: True if pdflatex is available, False otherwise
    """
    return shutil.which('pdflatex') is not None


def validate_csv_columns(csv_path, required_columns):
    """
    Validate that the CSV file has required columns.
    
    Args:
        csv_path (str): Path to CSV file
        required_columns (list): List of required column names
        
    Returns:
        tuple: (bool, list) - (is_valid, missing_columns)
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                return False, required_columns
            
            missing = [col for col in required_columns if col not in fieldnames]
            return len(missing) == 0, missing
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        return False, required_columns


def compile_pdf(template_path, output_name, name_value, sequence_value, seat_value, output_dir, keep_aux):
    """
    Compile a PDF using pdflatex with runtime parameters.
    
    Args:
        template_path (str): Path to LaTeX template file
        output_name (str): Output PDF name (without .pdf extension)
        name_value (str): Value for \\name command (LaTeX-escaped)
        sequence_value (str): Value for \\sequencenumber command (LaTeX-escaped)
        seat_value (str): Value for \\seat command (LaTeX-escaped)
        output_dir (str): Output directory path
        keep_aux (bool): Whether to keep auxiliary files
        
    Returns:
        tuple: (success, error_message)
    """
    # Timeout for pdflatex compilation (in seconds)
    PDFLATEX_TIMEOUT = 30
    
    # Build the pdflatex command
    # The LaTeX code string defines the three commands, then inputs the template
    latex_code = (
        f"\\def\\name{{{name_value}}}"
        f"\\def\\sequencenumber{{{sequence_value}}}"
        f"\\def\\seat{{{seat_value}}}"
        f"\\input{{{template_path}}}"
    )
    
    cmd = [
        'pdflatex',
        '-interaction=nonstopmode',
        '-halt-on-error',
        f'-output-directory={output_dir}',
        f'-jobname={output_name}',
        latex_code
    ]
    
    try:
        # Run pdflatex
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PDFLATEX_TIMEOUT,
            text=True
        )
        
        # Check if PDF was created
        pdf_path = os.path.join(output_dir, f"{output_name}.pdf")
        if os.path.exists(pdf_path):
            # Clean up auxiliary files if requested
            if not keep_aux:
                aux_extensions = ['.aux', '.log', '.out']
                for ext in aux_extensions:
                    aux_file = os.path.join(output_dir, f"{output_name}{ext}")
                    if os.path.exists(aux_file):
                        try:
                            os.remove(aux_file)
                        except Exception:
                            pass  # Ignore cleanup errors
            
            return True, None
        else:
            # PDF not created - compilation failed
            # Try to extract meaningful error from output
            output = result.stdout if result.stdout else result.stderr
            error_msg = extract_latex_error(output)
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, f"pdflatex timed out ({PDFLATEX_TIMEOUT} seconds)"
    except Exception as e:
        return False, str(e)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Generate personalized PDFs from LaTeX template and CSV data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s exam_template.tex roster.csv
  %(prog)s exam.tex students.csv --suffix CSE105S25 --output-dir pdfs/
  %(prog)s exam.tex students.csv --keep-aux

For more information, see the module docstring.
        """
    )
    
    parser.add_argument(
        'template',
        help='LaTeX template file with \\providecommand definitions'
    )
    parser.add_argument(
        'csv_file',
        help='CSV file with student data (columns: Student, Sequence, Notes)'
    )
    parser.add_argument(
        '--suffix',
        default='CSE20W26',
        help='Suffix for output filenames (default: CSE20W26)'
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Output directory for PDFs (default: current directory)'
    )
    parser.add_argument(
        '--keep-aux',
        action='store_true',
        help='Keep auxiliary LaTeX files (.aux, .log, etc.)'
    )
    parser.add_argument(
        '--extra',
        type=int,
        default=0,
        help='Number of extra PDFs to generate (default: 0)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Print debug information including LaTeX values'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    print("Validating inputs...")
    
    # Check template file exists
    if not os.path.isfile(args.template):
        print(f"Error: Template file not found: {args.template}", file=sys.stderr)
        sys.exit(1)
    
    # Check CSV file exists
    if not os.path.isfile(args.csv_file):
        print(f"Error: CSV file not found: {args.csv_file}", file=sys.stderr)
        sys.exit(1)
    
    # Check pdflatex is available
    if not check_pdflatex():
        print("Error: pdflatex not found. Please install LaTeX (e.g., TeX Live or MiKTeX)", file=sys.stderr)
        sys.exit(1)
    
    # Validate CSV has required columns
    required_columns = ['Student', 'Notes', 'ID']
    is_valid, missing = validate_csv_columns(args.csv_file, required_columns)
    if not is_valid:
        print(f"Error: CSV file missing required columns: {', '.join(missing)}", file=sys.stderr)
        print(f"Required columns: {', '.join(required_columns)}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Get absolute path to template for pdflatex
    template_path = os.path.abspath(args.template)
    
    # Read CSV and process students
    print(f"Reading student data from {args.csv_file}...")
    all_rows = []
    students = []
    skipped_rows = []
    
    with open(args.csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)
            # Only include rows where both Student name and ID are present
            student_name = row.get('Student', '').strip()
            student_id = row.get('ID', '').strip()
            
            if student_name and student_id:
                students.append(row)
            elif student_name and not student_id:
                # Name exists but no ID - skip this row but track it
                skipped_rows.append(student_name)

    total_students = len(students)
    if total_students == 0:
        print("Error: No valid students found in CSV file", file=sys.stderr)
        if skipped_rows:
            print(f"Note: {len(skipped_rows)} row(s) skipped (name but no ID)", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {total_students} valid student(s)")
    if skipped_rows:
        print(f"Skipping {len(skipped_rows)} row(s) with name but no ID")
    
    # Calculate padding width for index (based on total PDFs to generate)
    total_pdfs = total_students + args.extra
    padding_width = len(str(total_pdfs))
    
    # Process each student
    print("\nGenerating PDFs...")
    success_count = 0
    failure_count = 0
    failures = []
    
    for index, student in enumerate(students, start=1):
        # Extract data
        student_name = student.get('Student', 'Unknown')
        sequence = index
        seat = student.get('Notes', '')  # Notes column contains seat info
        
        # Convert all values to strings and strip whitespace
        student_name = str(student_name).strip()
        sequence = str(sequence).strip()
        seat = str(seat).strip()
        
        # Handle empty values - provide defaults for LaTeX template
        if not student_name:
            student_name = 'Unknown'
        if not sequence:
            sequence = 'TBD'
        if not seat:
            seat = 'TBD'
        
        # Sanitize name for filename
        safe_name = sanitize_filename(student_name)
        
        # Escape values for LaTeX
        name_latex = escape_latex(student_name)
        sequence_latex = escape_latex(sequence)
        seat_latex = escape_latex(seat)
        
        # Generate output filename
        padded_index = str(index).zfill(padding_width)
        output_name = f"{padded_index}.{safe_name}.{args.suffix}"
        
        # Print progress
        print(f"  [{index}/{total_students}] {student_name} -> {output_name}.pdf")
        
        # Debug output
        if args.debug:
            print(f"    DEBUG - Raw values:")
            print(f"      name: {repr(student_name)}")
            print(f"      sequence: {repr(sequence)}")
            print(f"      seat: {repr(seat)}")
            print(f"    DEBUG - LaTeX-escaped values:")
            print(f"      name: {repr(name_latex)}")
            print(f"      sequence: {repr(sequence_latex)}")
            print(f"      seat: {repr(seat_latex)}")
        
        # Compile PDF
        success, error = compile_pdf(
            template_path,
            output_name,
            name_latex,
            sequence_latex,
            seat_latex,
            output_dir,
            args.keep_aux
        )
        
        if success:
            success_count += 1
        else:
            failure_count += 1
            failures.append((student_name, output_name, error))

    # Process extra copies
    if args.extra > 0:
        print(f"\nGenerating {args.extra} extra PDF(s) not associated with specific students...")
        for i in range(total_students + 1, total_students + args.extra + 1): 
            # Use default data
            student_name = 'Extra'
            sequence = i
            seat = 'Extra'
            
            # Escape values for LaTeX
            name_latex = escape_latex(student_name)
            sequence_latex = escape_latex(str(sequence))
            seat_latex = escape_latex(seat)
            
            # Generate output filename
            padded_index = str(i).zfill(padding_width)
            output_name = f"{padded_index}.Extra.{args.suffix}"
            
            # Print progress
            print(f"  [{i}/{total_pdfs}] Extra copy -> {output_name}.pdf")
            
            # Compile PDF
            success, error = compile_pdf(
                template_path,
                output_name,
                name_latex,
                sequence_latex,
                seat_latex,
                output_dir,
                args.keep_aux
            )
            
            if success:
                success_count += 1
            else:
                failure_count += 1
                failures.append(('Extra', output_name, error))


    # Print summary
    print("\n" + "="*60)
    print("Summary:")
    print(f"  Successfully generated: {success_count} PDF(s)")
    print(f"  Failed: {failure_count} PDF(s)")
    
    if skipped_rows:
        print(f"  Skipped rows (name but no ID): {len(skipped_rows)}")
        for name in skipped_rows:
            print(f"    - {name}")
    
    if failures:
        print("\nFailures:")
        for name, filename, error in failures:
            print(f"  - {name} ({filename}.pdf)")
            if error:
                # Print first few lines of error, indented
                error_lines = error.split('\n')[:5]
                for line in error_lines:
                    if line.strip():
                        print(f"    {line[:120]}")
    
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if failure_count == 0 else 1)


if __name__ == '__main__':
    main()

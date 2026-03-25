# Grade Report PDF Generator

A Python script that generates personalized grade report PDFs from CSV data. Creates one PDF with one page per student, displaying their name, SID, email, and grade table.

## Features

- ✅ **Automatic column detection** - Finds student info (First Name, Last Name, SID, Email) automatically
- ✅ **Flexible CSV format** - Works with various CSV structures
- ✅ **Smart overflow handling** - Detects when too many columns won't fit and provides helpful error messages
- ✅ **Column selection** - Choose specific grade columns to include
- ✅ **Optional comments** - Add custom text below each student's grade table
- ✅ **Smart number formatting** - Numerical scores displayed with 2 decimal places
- ✅ **Professional formatting** - Clean, readable PDF layout with styled tables

## Requirements

Install the required Python package:

```bash
python -m pip install reportlab
```

**Note:** Use `python -m pip` instead of just `pip` to ensure the package is installed for the correct Python version. This is especially important if you have multiple Python installations (e.g., Anaconda + Framework Python).

## Usage

### Basic Usage (All Columns)

Generate a PDF with all grade columns:

```bash
python generate_grade_reports.py grades.csv output.pdf
```

### With Column Selection

Select specific grade columns to include:

```bash
python generate_grade_reports.py grades.csv output.pdf --columns "hw1,hw2,midterm,final"
```

Or use the short form:

```bash
python generate_grade_reports.py grades.csv output.pdf -c "T1,T2,T3,T4,Final"
```

### With Comments

Add a comment that will appear in the top right corner of each page (next to student info):

```bash
python generate_grade_reports.py grades.csv output.pdf -c "T1,T2,T3,T4" -m "Great work this quarter! Keep it up next term."
```

Or use the long form:

```bash
python generate_grade_reports.py grades.csv output.pdf --columns "Final,LetterGrade" --comment "Please see me during office hours if you have questions."
```

**Note:** The comment box appears in the top right corner next to student information. Longer comments may reduce the number of grade columns that can fit on the page. The script automatically adjusts the maximum column count when a comment is provided.

## CSV Format Requirements

The script automatically detects student information columns. Your CSV should have columns with names like:

- **First Name**: "First Name", "FirstName", "first_name", "fname"
- **Last Name**: "Last Name", "LastName", "last_name", "lname"  
- **SID**: "SID", "Student ID", "student_id", "id"
- **Email**: "Email", "e-mail", "mail"

All other columns are treated as grade data.

### Example CSV Structure

```csv
First Name,Last Name,SID,Email,hw1,hw2,midterm,final
John,Doe,A12345678,jdoe@example.com,95,88,92,90
Jane,Smith,A87654321,jsmith@example.com,92,94,89,93
```

## Error Handling

### Too Many Columns

If your CSV has too many grade columns to fit on one page, you'll see an error like:

```
======================================================================
ERROR: Too many columns to fit on one page!
======================================================================
Total grade columns: 40
Maximum columns per page: 7

Available grade columns:
    1. hw1
    2. hw2
    3. midterm
    ...

Please re-run with the --columns flag to select specific columns:
  python generate_grade_reports.py grades.csv output.pdf --columns "col1,col2,col3"
```

Simply re-run the script with the `--columns` flag to select which columns to include.

### Missing Student Info Columns

If the script can't detect student information columns:

```
Error: Could not detect student information columns.
Expected columns with names like: 'First Name', 'Last Name', 'SID', 'Email'
```

Make sure your CSV has at least some of these columns with recognizable names.

## Output

The script generates a single PDF file containing:

- **One page per student** with a two-column header layout:
  - **Left side**: Student name (large and bold), SID, and email
  - **Right side**: Optional comment box (if `--comment` is provided) with light gray background and border
- **Grade table** (below the header) with:
  - Assignment names in the first column
  - Scores/grades in the second column (numerical scores formatted to 2 decimal places)
  - Professional styling with alternating row colors
  - Clear borders and readable fonts

**Number Formatting:** The script automatically formats numerical scores to display exactly 2 decimal places (e.g., 95.5 becomes 95.50, 88.123 becomes 88.12). Non-numeric values like letter grades are displayed as-is.

**Comment Box:** When provided, the comment appears in a bordered box in the top right corner, aligned next to the student information. This creates a professional two-column header layout.

## Quick Start

First, ensure you have reportlab installed:
```bash
pip install reportlab
```

Then check the help:
```bash
python generate_grade_reports.py --help
```

## Detailed Examples

### Example 1: Generate with all columns (will likely error if too many)

```bash
python generate_grade_reports.py CSE20W26.grades.csv all_reports.pdf
```

If you have too many columns, you'll get a helpful error showing all available columns.

### Example 2: Test columns only

Generate a report with just the test scores:

```bash
python generate_grade_reports.py CSE20W26.grades.csv test_reports.pdf --columns "T1,T2,T3,T4"
```

### Example 3: Homework columns only

```bash
python generate_grade_reports.py CSE20W26.grades.csv hw_reports.pdf -c "hw1,hw2,hw3,hw4,hw5"
```

### Example 4: Summary grades

Include letter grade and computed scores:

```bash
python generate_grade_reports.py CSE20W26.grades.csv summary.pdf -c "LetterGrade,Grade,Finalgrade,TestGrade,HWGrade,Final"
```

### Example 5: Final exam with test averages

```bash
python generate_grade_reports.py CSE20W26.grades.csv final_report.pdf -c "T1grade,T2grade,T3grade,T4grade,Final"
```

### Example 6: Individual assignment scores

```bash
python generate_grade_reports.py CSE20W26.grades.csv detailed.pdf -c "hw1grade,hw2grade,hw3grade,hw4grade,hw5grade,T1grade,T2grade,T3grade,T4grade"
```

### Example 7: Reading quiz performance

```bash
python generate_grade_reports.py CSE20W26.grades.csv rq_reports.pdf -c "RQ1,RQ2,RQ3,RQ4,RQ5,RQ6,RQ7,RQ8,RQ9"
```

### Example 8: Custom combination

Mix and match any columns you need:

```bash
python generate_grade_reports.py CSE20W26.grades.csv custom.pdf -c "LetterGrade,T1,T2,T3,T4,Final,HWGrade"
```

### Example 9: With a comment message

Add encouraging feedback to each report:

```bash
python generate_grade_reports.py CSE20W26.grades.csv reports_with_msg.pdf -c "LetterGrade,Final,TestGrade,HWGrade" -m "Thank you for your hard work this quarter! Have a great break."
```

### Example 10: Midterm feedback with comment

```bash
python generate_grade_reports.py CSE20W26.grades.csv midterm.pdf -c "T1,T2" --comment "These are your first two test scores. Final exam will be comprehensive."
```

### What the output looks like:

```
Detected student info columns:
  first_name: First Name
  last_name: Last Name
  sid: SID
  email: Email

Found 35 grade columns
Using 7 selected columns

✓ Successfully generated PDF: test_reports.pdf
  Total students: 180
  Columns included: 7
```

## Tips

1. **Test with small subset**: Try with a small CSV first to verify formatting
2. **Column names**: Use exact column names from your CSV (case-sensitive for selection)
3. **Check detection**: The script shows which columns it detected - verify they're correct
4. **Maximum columns**: Typically 7-8 grade columns fit comfortably on a page

## Troubleshooting

**Q: Column not found error**
- Double-check spelling and case of column names
- Use `--columns` with exact names from your CSV

**Q: PDF looks cramped**
- Reduce number of columns with `--columns` flag
- Consider splitting into multiple reports (e.g., homework vs. exams)

**Q: Student name is blank**
- Verify CSV has "First Name" and "Last Name" columns
- Check that the data isn't in the wrong columns

## License

This script is provided as-is for educational purposes.

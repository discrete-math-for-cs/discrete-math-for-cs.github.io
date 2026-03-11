#!/usr/bin/env python3
"""
Script to generate outcomes.tex from weekly lesson files.
Aggregates learning outcomes from Week1.tex through Week10.tex
and creates a structured LaTeX document in notes/drafts/outcomes.tex

Includes cross-validation with outcomes.json to ensure consistency.
"""

import os
import re
import json
from datetime import datetime
from collections import defaultdict

# Path configuration (relative to script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LESSONS_DIR = os.path.join(SCRIPT_DIR, "notes/lessons")
DRAFTS_DIR = os.path.join(SCRIPT_DIR, "notes/drafts")
OUTPUT_FILE = os.path.join(DRAFTS_DIR, "outcomes.tex")
OUTCOMES_JSON = os.path.join(SCRIPT_DIR, "outcomes.json")

def extract_outcomes_from_file(filepath):
    """
    Extract learning outcomes from a weekly lesson file.
    Returns a list of tuples: (top_level_outcome, sub_outcomes_list)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the section "We will be learning and practicing to:"
    pattern = r'\\subsubsection\*\{We will be learning and practicing to:\}(.*?)\\subsubsection'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        # Try alternative ending pattern
        pattern = r'\\subsubsection\*\{We will be learning and practicing to:\}(.*?)\\end\{itemize\}'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return []
    
    outcomes_section = match.group(1)
    
    # Parse the hierarchical structure
    outcomes = []
    current_top_level = None
    current_sub_outcomes = []
    
    lines = outcomes_section.split('\n')
    inside_outer_itemize = False
    inside_inner_itemize = False
    
    for line in lines:
        stripped = line.strip()
        
        if '\\begin{itemize}' in stripped:
            if not inside_outer_itemize:
                inside_outer_itemize = True
            else:
                inside_inner_itemize = True
        elif '\\end{itemize}' in stripped:
            if inside_inner_itemize:
                inside_inner_itemize = False
                # Save current top-level outcome with its sub-outcomes
                if current_top_level:
                    outcomes.append((current_top_level, current_sub_outcomes[:]))
                    current_sub_outcomes = []
            else:
                inside_outer_itemize = False
        elif stripped.startswith('\\item ') and inside_outer_itemize:
            if inside_inner_itemize:
                # This is a sub-outcome
                sub_outcome = stripped[6:].strip()  # Remove '\item '
                if sub_outcome:
                    current_sub_outcomes.append(sub_outcome)
            else:
                # This is a top-level outcome
                # First save previous one if exists
                if current_top_level and current_sub_outcomes:
                    outcomes.append((current_top_level, current_sub_outcomes[:]))
                    current_sub_outcomes = []
                
                current_top_level = stripped[6:].strip()  # Remove '\item '
    
    return outcomes

def aggregate_outcomes_from_all_weeks():
    """
    Aggregate outcomes from all week files.
    Returns a dictionary mapping outcomes to the weeks they appear in.
    Structure: {top_level: {sub_outcome: [week_numbers]}}
    """
    all_outcomes = defaultdict(lambda: defaultdict(list))
    
    for week_num in range(1, 11):  # Week1 through Week10
        filename = f"Week{week_num}.tex"
        filepath = os.path.join(LESSONS_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found")
            continue
        
        print(f"Processing {filename}...")
        outcomes = extract_outcomes_from_file(filepath)
        
        for top_level, sub_outcomes in outcomes:
            for sub_outcome in sub_outcomes:
                all_outcomes[top_level][sub_outcome].append(week_num)
    
    return all_outcomes

def generate_latex_output(outcomes_dict, json_structure, only_in_weekly, only_in_json):
    """
    Generate LaTeX content for outcomes.tex following the hierarchical structure of outcomes.json
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create lookup for week information
    weeks_lookup = {}
    for top_level, sub_dict in outcomes_dict.items():
        for sub_outcome, weeks in sub_dict.items():
            weeks_lookup[sub_outcome] = weeks
    
    # Header (similar to definitions.tex) - build without f-string to avoid backslash issues
    latex_content = "% outcomes.tex\n"
    latex_content += "% Auto-generated file containing all learning outcomes\n"
    latex_content += f"% Generated on: {timestamp}\n"
    latex_content += "% \n"
    latex_content += "% This file aggregates learning outcomes from Week1.tex through Week10.tex\n"
    latex_content += "% in discrete-math-for-cs/notes/lessons/\n\n"
    latex_content += "\\documentclass[10pt, oneside]{article}\n\n"
    latex_content += "\\usepackage[letterpaper, scale=0.9, centering]{geometry}\n"
    latex_content += "\\usepackage{fancyhdr}\n"
    latex_content += "\\setlength{\\parindent}{0em}\n"
    latex_content += "\\setlength{\\parskip}{0.5em}\n\n"
    latex_content += "\\pagestyle{fancy}\n"
    latex_content += "\\fancyhf{}\n"
    latex_content += "\\renewcommand{\\headrulewidth}{0pt}\n"
    latex_content += "\\rfoot{{\\footnotesize Copyright Mia Minnes, Winter 2026}}\n\n"
    latex_content += "\\usepackage{titlesec}\n\n"
    latex_content += "\\author{CSE20W26}\n\n"
    latex_content += "\\input{../../resources/discrete-math-packages}\n\n"
    latex_content += "\\begin{document}\n"
    latex_content += "\\thispagestyle{fancy}\n\n"
    latex_content += "\\section*{Learning Outcomes for CSE 20}\n\n"
    latex_content += "This document aggregates all learning outcomes from the weekly lesson plans,\n"
    latex_content += "structured according to the hierarchy in outcomes.json.\n\n"
    latex_content += "\\tableofcontents\n\n"
    latex_content += "\\newpage\n\n"
    
    # Process the 3 top-level categories from JSON
    for top_level_key, top_level_value in json_structure.items():
        top_level_desc = top_level_value.get('Description', '')
        latex_content += "\\section{" + top_level_key + "}\n\n"
        if top_level_desc:
            latex_content += top_level_desc + "\n\n"
        
        # Process second-level categories (should be 2 for each top-level)
        if 'Children' in top_level_value:
            for second_level_key, second_level_value in top_level_value['Children'].items():
                second_level_desc = second_level_value.get('Description', '')
                latex_content += "\\subsection{" + second_level_key + "}\n\n"
                if second_level_desc:
                    latex_content += second_level_desc + "\n\n"
                
                # Process leaf-level outcomes
                if 'Children' in second_level_value:
                    latex_content += "\\begin{itemize}\n"
                    for leaf_key, leaf_value in second_level_value['Children'].items():
                        if isinstance(leaf_value, dict) and 'Description' in leaf_value:
                            leaf_desc = leaf_value['Description']
                            latex_content += "\\item " + leaf_desc + "\n"
                            
                            # Add week information if available
                            if leaf_desc in weeks_lookup:
                                weeks = weeks_lookup[leaf_desc]
                                weeks_str = ", ".join(["Week " + str(w) for w in sorted(weeks)])
                                latex_content += "% Appears in: " + weeks_str + "\n"
                            latex_content += "\n"
                    latex_content += "\\end{itemize}\n\n"
                
                latex_content += "\\vfill\n\n"
        
        latex_content += "\\newpage\n\n"
    
    # Add section for outcomes only in weekly files
    if only_in_weekly:
        latex_content += "\\section*{Outcomes Found Only in Weekly Files}\n\n"
        latex_content += "The following outcomes appear in weekly lesson files but not in outcomes.json.\n"
        latex_content += "These may need to be added to outcomes.json.\n\n"
        latex_content += "\\begin{itemize}\n"
        for outcome in sorted(only_in_weekly):
            latex_content += "\\item " + outcome + "\n"
            if outcome in weeks_lookup:
                weeks = weeks_lookup[outcome]
                weeks_str = ", ".join(["Week " + str(w) for w in sorted(weeks)])
                latex_content += "% Appears in: " + weeks_str + "\n"
            latex_content += "\n"
        latex_content += "\\end{itemize}\n\n"
        latex_content += "\\vfill\n\\newpage\n\n"
    
    # Add section for outcomes only in JSON
    if only_in_json:
        latex_content += "\\section*{Outcomes Found Only in outcomes.json}\n\n"
        latex_content += "The following outcomes appear in outcomes.json but not in weekly lesson files.\n"
        latex_content += "These may need to be added to weekly files or removed from outcomes.json.\n\n"
        latex_content += "\\begin{itemize}\n"
        for outcome in sorted(only_in_json):
            latex_content += "\\item " + outcome + "\n\n"
        latex_content += "\\end{itemize}\n\n"
    
    # Footer
    latex_content += "\\end{document}\n"
    
    return latex_content

def load_outcomes_from_json():
    """
    Load the full hierarchical structure from outcomes.json.
    Returns: (full_structure, flat_set_of_leaf_outcomes)
    """
    with open(OUTCOMES_JSON, 'r', encoding='utf-8') as f:
        outcomes_json = json.load(f)
    
    # Extract flat set for validation
    flat_outcomes = set()
    
    def extract_leaf_outcomes(node):
        """Recursively extract leaf-level outcomes"""
        if isinstance(node, dict):
            if 'Children' in node:
                for child_value in node['Children'].values():
                    extract_leaf_outcomes(child_value)
            elif 'Description' in node:
                flat_outcomes.add(node['Description'])
    
    for top_level_value in outcomes_json.values():
        extract_leaf_outcomes(top_level_value)
    
    return outcomes_json, flat_outcomes

def cross_validate_outcomes(extracted_outcomes, json_flat_outcomes):
    """
    Cross-validate extracted outcomes against outcomes.json.
    Returns: (only_in_weekly, only_in_json, validation_passed)
    """
    print("\n" + "="*70)
    print("CROSS-VALIDATION WITH outcomes.json")
    print("="*70)
    
    # Flatten extracted outcomes for comparison
    extracted_set = set()
    for top_level, sub_dict in extracted_outcomes.items():
        for sub_outcome in sub_dict.keys():
            extracted_set.add(sub_outcome)
    
    # Find outcomes in weekly files but not in JSON
    only_in_weekly = extracted_set - json_flat_outcomes
    
    # Find outcomes in JSON but not in weekly files
    only_in_json = json_flat_outcomes - extracted_set
    
    # Report results
    validation_passed = True
    
    if only_in_weekly:
        print("\n⚠️  OUTCOMES IN WEEKLY FILES BUT NOT IN outcomes.json:")
        print("-" * 70)
        for outcome in sorted(only_in_weekly):
            print(f"  - {outcome}")
        validation_passed = False
    
    if only_in_json:
        print("\n⚠️  OUTCOMES IN outcomes.json BUT NOT IN WEEKLY FILES:")
        print("-" * 70)
        for outcome in sorted(only_in_json):
            print(f"  - {outcome}")
        validation_passed = False
    
    if validation_passed:
        print("\n✓ VALIDATION PASSED: All outcomes are consistent!")
        print(f"  Total outcomes validated: {len(extracted_set)}")
    else:
        print("\n✗ VALIDATION FAILED: Inconsistencies found between weekly files and outcomes.json")
        print(f"  Outcomes in weekly files: {len(extracted_set)}")
        print(f"  Outcomes in outcomes.json: {len(json_flat_outcomes)}")
        print(f"  Outcomes only in weekly files: {len(only_in_weekly)}")
        print(f"  Outcomes only in outcomes.json: {len(only_in_json)}")
    
    print("="*70 + "\n")
    
    return only_in_weekly, only_in_json, validation_passed

def main():
    """Main function to generate outcomes.tex"""
    print("Starting outcomes catalog generation...")
    print(f"Looking for week files in: {LESSONS_DIR}")
    
    # Aggregate outcomes
    outcomes_dict = aggregate_outcomes_from_all_weeks()
    
    if not outcomes_dict:
        print("Error: No outcomes found!")
        return
    
    print(f"\nFound {len(outcomes_dict)} top-level outcome categories")
    total_sub_outcomes = sum(len(subs) for subs in outcomes_dict.values())
    print(f"Total unique sub-outcomes: {total_sub_outcomes}")
    
    # Cross-validate with outcomes.json
    print(f"\nLoading outcomes.json from: {OUTCOMES_JSON}")
    json_structure, json_flat_outcomes = load_outcomes_from_json()
    only_in_weekly, only_in_json, validation_passed = cross_validate_outcomes(outcomes_dict, json_flat_outcomes)
    
    # Generate LaTeX
    latex_content = generate_latex_output(outcomes_dict, json_structure, only_in_weekly, only_in_json)
    
    # Write to file
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    print(f"\n✓ Successfully generated: {OUTPUT_FILE}")
    print(f"  File size: {len(latex_content)} characters")

if __name__ == "__main__":
    main()

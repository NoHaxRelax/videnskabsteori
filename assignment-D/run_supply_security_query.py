#!/usr/bin/env python3
"""
Supply Security Query
This script queries the Energy Islands corpus for statements related to 
energy supply security using multiple alternative formulations.
"""

import pandas as pd

# Load the CSV file
print("Loading data...")
df = pd.read_csv('Actor statement corpus - dataset.csv')

# Set 'Year' column to int
df['Year'] = df['Year'].replace('', pd.NA)
df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype(pd.Int64Dtype())

print(f'Data loaded. Total statements in corpus: {len(df)}')
print()

# Build the query using the pipe operator (|) for OR logic
# This searches for any of the alternative formulations of "energy supply security"
print("=" * 80)
print("SUPPLY SECURITY QUERY")
print("=" * 80)
print()
print("Searching for the following terms (case-insensitive):")
terms_list = [
    'supply security',
    'supply reliability',
    'security of supply',
    'power adequacy',
    'electricity supply security',
    'energy security',
    'energy independence',
    'stable electricity supply',
    'stable electricity',
    'stable energy',
    'forsyningssikkerhed'
]
for i, term in enumerate(terms_list, 1):
    print(f"  {i}. {term}")

print()

query_terms = '|'.join(terms_list)

condition = df['Statement'].str.contains(query_terms, case=False, na=False)

# Calculate statistics
df_copy = df.copy()
df_copy['filtered'] = condition
filtered_counts = df_copy['filtered'].value_counts()

statements_matching = filtered_counts.get(True, 0)
statements_not_matching = filtered_counts.get(False, 0)
total_statements = len(df_copy)
percentage_matching = (statements_matching / total_statements * 100)

print("=" * 80)
print("QUERY RESULTS")
print("=" * 80)
print()
print(f"✓ Statements matching the query: {statements_matching}")
print(f"✗ Statements NOT matching the query: {statements_not_matching}")
print(f"  Total statements: {total_statements}")
print(f"  Percentage matching: {percentage_matching:.2f}%")
print()

# Get the filtered dataframe
df_filtered = df[condition].copy()

print("=" * 80)
print("FIRST 5 MATCHING STATEMENTS")
print("=" * 80)

for idx, row in df_filtered.head(5).iterrows():
    print()
    print(f"ID: {row['id']}")
    print(f"Actor: {row['Actor']}")
    print(f"Representative of: {row['Representative of']}")
    print(f"Year: {row['Year']}")
    print(f"Statement (first 250 chars):")
    print(f"  {row['Statement'][:250]}...")
    print("-" * 80)

print()
print("=" * 80)
print("TOP 10 ACTORS DISCUSSING SUPPLY SECURITY")
print("=" * 80)
print()
actor_counts = df_filtered['Actor'].value_counts().head(10)
for actor, count in actor_counts.items():
    print(f"  {count:3d} - {actor}")

print()
print("=" * 80)
print("EXPORT RESULTS")
print("=" * 80)

# Save the filtered results to a new CSV file
output_file = 'supply_security_statements.csv'
df_filtered.to_csv(output_file, index=False)
print(f"\n✓ Saved {len(df_filtered)} statements to '{output_file}'")
print()

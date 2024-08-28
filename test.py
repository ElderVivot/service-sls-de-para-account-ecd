from src.read_lines_and_processed import ReadLinesAndProcessed

with open(f'data/big2.txt', 'r', encoding='cp1252', errors='ignore') as f:
    ReadLinesAndProcessed(f).executeJobMainAsync()

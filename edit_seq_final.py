import sys

def process(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('pick '):
                f.write(line.replace('pick ', 'reword '))
            else:
                f.write(line)

if __name__ == '__main__':
    process(sys.argv[1])

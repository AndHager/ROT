import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import tikzplotlib

# use latex for font rendering
mpl.rcParams['text.usetex'] = True

def sort_dict(d, threshold):
    vals = [
        val 
        for val in d.items()
    ]
    return sorted(vals, key=lambda x:x[0], reverse=False)[:threshold]

def plot_val(base, val, name, color):
    # Plot static data
    base_val = {
        base[i]: val[i]
        for i in range(len(base))
    }
    sort_base_val = sort_dict(base_val, len(base))
    print(sort_base_val)
    srt_base = [e[0] for e in sort_base_val]
    srt_val = [e[1]/1000 for e in sort_base_val]
    plt.scatter(srt_base, srt_val, color=color, label=name, alpha=0.7)

    # Data for plotting
    np_base = np.array(srt_base)
    np_val = np.array(srt_val)

    # Perform least squares linear regression
    # Fit line: y = m * x + b
    A = np.vstack([np_base, np.ones(len(np_base))]).T
    m, b = np.linalg.lstsq(A, np_val, rcond=None)[0]

    # Generate the best-fit line
    x_fit = np.linspace(min(np_base), max(np_base), 500)
    y_fit = m * x_fit + b

    # Least squares best-fit line
    # f" Fit: y = {m:.2f}x + {b:.2f}"
    plt.plot(x_fit, y_fit, color=color, label=f"", linewidth=2)
    
tex = False

# Read data from file
filename = 'out/performance_data.csv'
targets = []

instruction_count = []
parse_time = []

dynamic_instruction_count = []
dynamic_parse_time = []

generation_time = []
merge_time = []
selection_time = []

# Parse the CSV file
with open(filename, 'r') as file:
    reader = csv.DictReader(file, delimiter=',')
    for row in reader:
        targets.append(row['Target'])
    
        instruction_count.append(int(row['InstructionCount']))
        parse_time.append(int(row['ParseTime']))
        
        dynamic_instruction_count.append(int(row['DynamicInstructionCount']))
        dynamic_parse_time.append(int(row['DynamicParseTime']))
        
        generation_time.append(int(row['GenerationTime']))
        merge_time.append(int(row['MergeTime']))
        selection_time.append(int(row['SelectionTime']))


target_count = len(targets)

# Create figure and axis
x = np.arange(target_count)
width = 0.15  # Bar width

# Create a scatter plot
plt.figure(figsize=(8, 4))

plot_val(instruction_count, parse_time, 'Parsing', 'seagreen')
plot_val(instruction_count, generation_time, 'Generation', 'cadetblue')
plot_val(instruction_count, merge_time, 'Merge', 'navy')
plot_val(instruction_count, selection_time, 'Selection', 'purple')

# Customizations
plt.xlabel("Instruction Count", fontsize=12)
plt.ylabel("Execution Time (Milliseconds)", fontsize=12)
# plt.title("Parse Time vs Instruction Count", fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()

# Display the graph
#plt.show()

# plt.legend().remove()

fig_name = 'performance'
plt.savefig(str(fig_name) + '.pdf', format='pdf', transparent=True)
if tex:
    tikzplotlib.save(fig_name + '.tex')

plt.close()

